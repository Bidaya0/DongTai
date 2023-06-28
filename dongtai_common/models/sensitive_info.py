######################################################################
# @author      : bidaya0 (bidaya0@$HOSTNAME)
# @file        : sensitive_info
# @created     : 星期五 11月 19, 2021 11:02:19 CST
#
# @description :
######################################################################

from django.db import models
from dongtai_common.models.strategy import IastStrategyModel
from dongtai_common.models.user import User
import time


class IastPatternType(models.Model):
    name = models.CharField(max_length=255)
    id = models.IntegerField(default=0, db_column='value')
    logi_id = models.BigAutoField(primary_key=True, db_column='id')

    class Meta:
        db_table = 'iast_pattern_type'


class IastSensitiveInfoRule(models.Model):
    user = models.ForeignKey(User, models.DO_NOTHING)
    strategy = models.ForeignKey(IastStrategyModel, models.DO_NOTHING)
    pattern_type = models.ForeignKey(IastPatternType, models.DO_NOTHING)
    pattern = models.CharField(default=None, max_length=255)
    status = models.IntegerField(default=None)
    latest_time = models.IntegerField(default=lambda: int(time.time()))

    class Meta:
        db_table = 'iast_sensitive_info_rule'
