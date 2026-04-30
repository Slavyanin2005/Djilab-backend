from django.db.models import Max


def get_next_id(model_class):
    max_id = model_class.objects.aggregate(Max("id"))["id__max"]
    return (max_id or 0) + 1
