from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_parkingrecord")]
    operations = [
        migrations.AddField(
            model_name="vehicle", name="registration_active",
            field=models.BooleanField(default=True),
        ),
    ]
