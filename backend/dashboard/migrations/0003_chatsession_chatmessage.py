from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0002_dataanalysisreport_devicenode_alarmrecord_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="会话ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "聊天会话",
                "verbose_name_plural": "聊天会话",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[("user", "用户"), ("assistant", "助手"), ("system", "系统")],
                        max_length=16,
                        verbose_name="角色",
                    ),
                ),
                ("content", models.TextField(verbose_name="内容")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="发送时间")),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="dashboard.chatsession",
                        verbose_name="所属会话",
                    ),
                ),
            ],
            options={
                "verbose_name": "聊天消息",
                "verbose_name_plural": "聊天消息",
                "ordering": ["created_at"],
            },
        ),
    ]
