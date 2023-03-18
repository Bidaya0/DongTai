import logging
import json

from django.db.models import Q, F, Count
from django.utils.translation import gettext_lazy as _
from dongtai_common.endpoint import UserEndPoint, R
from rest_framework.viewsets import ViewSet
from dongtai_common.models.agent import IastAgent
from dongtai_common.models.strategy import IastStrategyModel
from dongtai_common.models.vulnerablity import IastVulnerabilityModel
from django.core.cache import cache
from dongtai_web.utils import extend_schema_with_envcheck, get_response_serializer
from dongtai_common.models.dast_integration import IastDastIntegration
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.serializers import ValidationError

logger = logging.getLogger('dongtai-webapi')


class VulsPageArgsSerializer(serializers.Serializer):
    page_size = serializers.IntegerField(default=20,
                                         help_text=_('Number per page'))
    page = serializers.IntegerField(default=1, help_text=_('Page index'))
    keyword = serializers.CharField(help_text=_('keyword'), required=False)
    project_id = serializers.ListField(child=serializers.IntegerField(),
                                       required=False)
    project_version_id = serializers.IntegerField(required=False)
    bind_project_id = serializers.IntegerField(required=False)
    vul_level_id = serializers.ListField(child=serializers.IntegerField(),
                                         required=False)
    vul_type = serializers.ListField(child=serializers.CharField(),
                                     required=False)
    order_by_field = serializers.ChoiceField(['create_time', 'vul_level'],
                                             default='create_time')
    order_by_order = serializers.ChoiceField(['desc', 'asc'], default='desc')


class VulsSummaryArgsSerializer(VulsPageArgsSerializer):

    class Meta:
        fields = ['bind_project_id', 'project_id', 'project_version_id']


class VulsDeleteArgsSerializer(VulsPageArgsSerializer):
    vul_id = serializers.ListField(child=serializers.IntegerField(),
                                   required=False)


class VulsResArgsSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name')
    project_version_name = serializers.CharField(
        source='project_version.version_name')
    vul_level_name = serializers.CharField(source='vul_level.name')

    class Meta:
        model = IastDastIntegration
        fields = [
            'id',
            'vul_name',
            'detail',
            'vul_level',
            'payload',
            'target',
            'vul_type',
            'dast_tag',
            'request_messages',
            'urls',
            'create_time',
            'latest_time',
            'project',
            'project_id',
            'project_version',
            'project_version_id',
            'project_name',
            'project_version_name',
            'vul_level_name',
            'vul_level_id',
        ]

class DastVulsEndPoint(UserEndPoint, viewsets.ViewSet):

    @extend_schema_with_envcheck(request=VulsSummaryArgsSerializer,
                                 summary=_('Dast Vul Summary'),
                                 description=_("Dast Vul Summary"),
                                 tags=[_('Dast Vul')])
    def summary(self, request):
        ser = VulsSummaryArgsSerializer(data=request.data)
        try:
            if ser.is_valid(True):
                pass
        except ValidationError as e:
            return R.failure(data=e.detail)
        department = request.user.get_relative_department()
        q = Q(project__department__in=department)
        if 'bind_project_id' in ser.validated_data:
            q = q & Q(project_id=ser.validated_data['bind_project_id'])
        if 'project_version_id' in ser.validated_data:
            q = q & Q(project_id=ser.validated_data['project_version_id'])
        vul_level_info = IastDastIntegration.objects.filter(q).values(
            'vul_level__name',
            'vul_level_id').annotate(total=Count('vul_level_id')).all()
        vul_type_info = IastDastIntegration.objects.filter(q).values(
            'vul_type').annotate(total=Count('vul_type')).all()
        project_info = IastDastIntegration.objects.filter(q).values(
            'project__name',
            'project_id').annotate(total=Count('project_id')).all()
        return R.success(
            data={
                "vul_level": list(vul_level_info),
                "vul_type": list(vul_type_info),
                "project_info": list(project_info),
            })

    @extend_schema_with_envcheck(request=VulsPageArgsSerializer,
                                 summary=_('Dast Vul list'),
                                 description=_("Dast Vul list"),
                                 tags=[_('Dast Vul')])
    def page(self, request):
        ser = VulsPageArgsSerializer(data=request.data)
        try:
            if ser.is_valid(True):
                pass
        except ValidationError as e:
            return R.failure(data=e.detail)
        department = request.user.get_relative_department()
        q = Q(project__department__in=department)
        if 'vul_level_id' in ser.validated_data:
            q = q & Q(vul_level_id__in=ser.validated_data['vul_level_id'])
        if 'bind_project_id' in ser.validated_data:
            q = q & Q(project_id=ser.validated_data['bind_project_id'])
        if 'vul_type' in ser.validated_data:
            q = q & Q(vul_type__in=ser.validated_data['vul_type'])
        if 'project_id' in ser.validated_data:
            q = q & Q(project_id__in=ser.validated_data['project_id'])
        if 'project_version_id' in ser.validated_data:
            q = q & Q(project_version_id=ser.validated_data['project_version_id'])
        if 'keyword' in ser.validated_data:
            q = q & Q(keyword__contains=ser.validated_data['keyword'])
        if ser.validated_data['order_by_order'] == 'desc':
            order_by_func = F(ser.validated_data['order_by_field']).desc()
        else:
            order_by_func = F(ser.validated_data['order_by_field']).asc()
        page_summary, dastvuls = self.get_paginator(
            IastDastIntegration.objects.filter(q).order_by(
                order_by_func).all(), ser.validated_data['page'],
            ser.validated_data['page_size'])
        return R.success(data=VulsResArgsSerializer(dastvuls, many=True).data,
                         page=page_summary)

    @extend_schema_with_envcheck(summary=_('Dast Vul detail'),
                                 description=_("Dast Vul detail"),
                                 tags=[_('Dast Vul')])
    def single(self, request, pk):
        department = request.user.get_relative_department()
        q = Q(project__department__in=department) & Q(pk=pk)
        dastvul = IastDastIntegration.objects.filter(q).first()
        return R.success(data=VulsResArgsSerializer(dastvul).data)

    @extend_schema_with_envcheck(summary=_('Dast Vul delete'),
                                 description=_("Dast Vul delete"),
                                 tags=[_('Dast Vul')])
    def delete(self, request):
        ser = VulsDeleteArgsSerializer(data=request.data)
        try:
            if ser.is_valid(True):
                pass
        except ValidationError as e:
            return R.failure(data=e.detail)
        department = request.user.get_relative_department()
        q = Q(project__department__in=department) & Q(
            pk__in=ser.validated_data['vul_id'])
        dastvul = IastDastIntegration.objects.filter(q).values().first()
        return R.success(data=dastvul)