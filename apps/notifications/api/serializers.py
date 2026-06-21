from rest_framework import serializers

from apps.notifications.models import Notification, ReportRun


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "channel", "subject", "body", "status", "scheduled_for",
                  "sent_at", "created_at"]
        read_only_fields = fields


class ReportRunSerializer(serializers.ModelSerializer):
    output_url = serializers.SerializerMethodField()

    class Meta:
        model = ReportRun
        fields = ["id", "report_type", "parameters", "status", "row_count",
                  "error", "output_url", "created_at", "finished_at"]
        read_only_fields = ["status", "row_count", "error", "output_url",
                            "finished_at", "created_at"]

    def get_output_url(self, obj):
        if not obj.output_file:
            return None
        request = self.context.get("request")
        url = obj.output_file.url
        return request.build_absolute_uri(url) if request else url
