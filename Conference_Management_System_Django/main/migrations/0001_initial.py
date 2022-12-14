# Generated by Django 2.2.1 on 2022-10-21 05:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('paper_id', models.TextField(primary_key=True, serialize=False)),
                ('paper_name', models.TextField(default='')),
                ('paper_details', models.TextField(default='')),
                ('acceptance_state', models.TextField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.TextField(primary_key=True, serialize=False)),
                ('login_email', models.TextField()),
                ('login_pw', models.TextField()),
                ('name', models.TextField()),
                ('is_suspended', models.BooleanField(default=False)),
                ('user_type', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Reviews',
            fields=[
                ('review_id', models.TextField(primary_key=True, serialize=False)),
                ('review_details', models.TextField()),
                ('reviewer_rating', models.TextField()),
                ('author_rating', models.TextField()),
                ('paper_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Paper')),
                ('reviewer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.User')),
            ],
        ),
        migrations.CreateModel(
            name='Reviewer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_papers', models.TextField(default=5)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.User')),
            ],
        ),
        migrations.CreateModel(
            name='ReviewComments',
            fields=[
                ('comment_id', models.TextField(primary_key=True, serialize=False)),
                ('comment_text', models.TextField()),
                ('commenter_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.User')),
                ('review_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Reviews')),
            ],
        ),
        migrations.CreateModel(
            name='Bids',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_bidding', models.BooleanField(default=True)),
                ('paper_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Paper')),
                ('reviewer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.User')),
            ],
        ),
        migrations.CreateModel(
            name='Authors',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.User')),
                ('paper_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Paper')),
            ],
        ),
    ]
