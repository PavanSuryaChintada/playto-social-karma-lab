# Generated manually for karma ledger model.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('comments', '0001_initial'),
        ('posts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KarmaEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_type', models.CharField(choices=[('post_like', 'Post Like'), ('comment_like', 'Comment Like')], max_length=20)),
                ('points', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='karma_events_performed', to=settings.AUTH_USER_MODEL)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='karma_events_received', to=settings.AUTH_USER_MODEL)),
                ('source_comment_like', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='karma_event', to='comments.commentlike')),
                ('source_post_like', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='karma_event', to='posts.postlike')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['created_at'], name='karma_karmae_created_08f2c1_idx'),
                    models.Index(fields=['recipient', 'created_at'], name='karma_karmae_recipie_9a7ba2_idx'),
                ],
                'constraints': [
                    models.CheckConstraint(condition=models.Q(('points__gt', 0)), name='karma_points_gt_zero'),
                    models.CheckConstraint(condition=models.Q(models.Q(('source_type', 'post_like'), ('source_post_like__isnull', False), ('source_comment_like__isnull', True)), models.Q(('source_type', 'comment_like'), ('source_comment_like__isnull', False), ('source_post_like__isnull', True)), _connector='OR'), name='karma_source_matches_type'),
                ],
            },
        ),
    ]
