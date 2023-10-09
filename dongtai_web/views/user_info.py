#!/usr/bin/env python

import logging

from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from dongtai_common.endpoint import R, UserEndPoint
from dongtai_common.utils.request_type import Request
from dongtai_conf.settings import SCA_SETUP

logger = logging.getLogger("django")


class UserInfoEndpoint(UserEndPoint):
    name = "api-v1-user-info"
    description = _("User Info")

    @extend_schema(
        summary=_("User Info"),
        tags=[_("User")],
    )
    def get(self, request: Request):
        user = request.user
        group = Group.objects.filter(user=user).order_by("-id").first()

        return R.success(
            data={
                "userid": user.id if not user.is_anonymous else -1,
                "username": user.get_username(),
                "role": 3
                if group is None
                else 2
                if group.name == "talent_admin"
                else 1
                if group.name == "system_admin"
                else 0,
                "role_name": "" if group is None else group.name,
                "role_id": user.role_id,
                "sca_setup": not SCA_SETUP,
                "enable_totp": bool(user.totp_secret),
                "is_wait_binding": user.role_id == 11,
                "is_bind_ldap": bool(user.ldap_dn),
            }
        )
