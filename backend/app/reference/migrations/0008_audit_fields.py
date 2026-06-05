import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0007_alter_country_id_alter_department_id_and_more"),
    ]

    operations = [
        # Country — add audit fields
        migrations.AddField(
            model_name="country",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="country",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="country",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="country",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        # Department — add audit fields
        migrations.AddField(
            model_name="department",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="department",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="department",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="department",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        # Parcours — add audit fields
        migrations.AddField(
            model_name="parcours",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="parcours",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="parcours",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="parcours",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        # Level — remove is_active, add created_by/updated_by
        migrations.RemoveField(
            model_name="level",
            name="is_active",
        ),
        migrations.RemoveIndex(
            model_name="level",
            name="reference_l_is_acti_1a5854_idx",
        ),
        migrations.AddField(
            model_name="level",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="level",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
