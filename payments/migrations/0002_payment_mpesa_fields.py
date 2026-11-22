from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='phone',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='payment',
            name='checkout_request_id',
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name='payment',
            name='merchant_request_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='payment',
            name='result_desc',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
