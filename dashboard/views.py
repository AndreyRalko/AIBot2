import csv
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from knowledge.models import IndexBuild, KnowledgeDocument
from qa.models import QuestionLog
from rag.indexer import rebuild_index

from .forms import KnowledgeTextForm, KnowledgeUploadForm

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)

PERIOD_CHOICES = (
    ("all", "За всё время"),
    ("7d", "7 дней"),
    ("30d", "30 дней"),
    ("90d", "90 дней"),
    ("year", "Год"),
    ("custom", "Свои даты"),
)


def _period_filter(request):
    period = request.GET.get("period") or "all"
    if period not in {item[0] for item in PERIOD_CHOICES}:
        period = "all"
    tz = timezone.get_current_timezone()
    now = timezone.now()
    start = end = None
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")

    if period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "90d":
        start = now - timedelta(days=90)
    elif period == "year":
        start = now - timedelta(days=365)
    elif period == "custom":
        parsed_from = parse_date(date_from)
        parsed_to = parse_date(date_to)
        if parsed_from:
            start = timezone.make_aware(datetime.combine(parsed_from, time.min), tz)
        if parsed_to:
            start_of_next = datetime.combine(parsed_to, time.min) + timedelta(days=1)
            end = timezone.make_aware(start_of_next, tz)

    qs = QuestionLog.objects.all()
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lt=end)
    return period, date_from, date_to, qs, start, end or now


def _read_uploaded_text(uploaded) -> str:
    raw = uploaded.read()
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return raw.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").strip()


@login_required
@staff_required
def home(request):
    period, date_from, date_to, scoped, start, end = _period_filter(request)
    span_days = (end - start).days if start else 400
    trunc = TruncMonth("created_at") if span_days > 90 else TruncDate("created_at")

    daily = list(
        scoped.annotate(day=trunc)
        .values("day")
        .annotate(
            total=Count("id"),
            unanswered=Count("id", filter=Q(is_unanswered=True)),
        )
        .order_by("day")
    )
    languages = list(scoped.values("language").annotate(total=Count("id")).order_by("-total"))
    language_labels = {"ru": "Русский", "kk": "Қазақша"}
    top_questions = list(
        scoped.values("question")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )

    last_index = IndexBuild.objects.first()
    period_label = dict(PERIOD_CHOICES).get(period, "За всё время")
    if period == "custom" and (date_from or date_to):
        period_label = f"{date_from or '…'} — {date_to or '…'}"

    context = {
        "period": period,
        "period_choices": PERIOD_CHOICES,
        "period_label": period_label,
        "date_from": date_from,
        "date_to": date_to,
        "chart_by_month": span_days > 90,
        "total_questions": scoped.count(),
        "unanswered_count": scoped.filter(is_unanswered=True).count(),
        "active_docs": KnowledgeDocument.objects.filter(is_active=True).count(),
        "last_index": last_index,
        "daily_json": [
            {
                "day": (
                    row["day"].strftime("%Y-%m")
                    if span_days > 90
                    else row["day"].strftime("%Y-%m-%d")
                )
                if row["day"]
                else "",
                "total": row["total"],
                "unanswered": row["unanswered"],
            }
            for row in daily
        ],
        "languages_json": [
            {
                "language": row["language"],
                "label": language_labels.get(row["language"], row["language"] or "—"),
                "total": row["total"],
            }
            for row in languages
        ],
        "top_questions": top_questions,
        "latest_questions": scoped[:8],
    }
    return render(request, "dashboard/home.html", context)


@login_required
@staff_required
def knowledge_page(request):
    upload_form = KnowledgeUploadForm()
    text_form = KnowledgeTextForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "upload":
            upload_form = KnowledgeUploadForm(request.POST, request.FILES)
            if upload_form.is_valid() and upload_form.cleaned_data.get("file"):
                doc = upload_form.save(commit=False)
                uploaded = upload_form.cleaned_data["file"]
                doc.original_name = uploaded.name
                doc.content = _read_uploaded_text(uploaded)
                uploaded.seek(0)
                doc.uploaded_by = request.user
                if not doc.title:
                    doc.title = uploaded.name
                doc.save()
                result = rebuild_index()
                if result["ok"]:
                    messages.success(
                        request,
                        f"Документ сохранён, индекс обновлён ({result['chunks']} фрагментов).",
                    )
                else:
                    messages.warning(request, f"Документ сохранён, но индекс не собран: {result['error']}")
                return redirect("dashboard:knowledge")
        elif action == "paste":
            text_form = KnowledgeTextForm(request.POST)
            if text_form.is_valid():
                KnowledgeDocument.objects.create(
                    title=text_form.cleaned_data["title"],
                    content=text_form.cleaned_data["content"].strip(),
                    uploaded_by=request.user,
                )
                result = rebuild_index()
                if result["ok"]:
                    messages.success(
                        request,
                        f"Текст добавлен, индекс обновлён ({result['chunks']} фрагментов).",
                    )
                else:
                    messages.warning(request, f"Текст сохранён, но индекс не собран: {result['error']}")
                return redirect("dashboard:knowledge")

    documents = KnowledgeDocument.objects.select_related("uploaded_by")
    return render(
        request,
        "dashboard/knowledge.html",
        {
            "upload_form": upload_form,
            "text_form": text_form,
            "documents": documents,
            "last_index": IndexBuild.objects.first(),
        },
    )


@login_required
@staff_required
@require_POST
def knowledge_delete(request, pk):
    get_object_or_404(KnowledgeDocument, pk=pk).delete()
    result = rebuild_index()
    if result["ok"]:
        messages.success(request, "Документ удалён, индекс пересобран.")
    else:
        messages.info(request, f"Документ удалён. {result['error']}")
    return redirect("dashboard:knowledge")


@login_required
@staff_required
@require_POST
def knowledge_toggle(request, pk):
    doc = get_object_or_404(KnowledgeDocument, pk=pk)
    doc.is_active = not doc.is_active
    doc.save(update_fields=["is_active", "updated_at"])
    rebuild_index()
    messages.success(request, "Статус документа обновлён, индекс пересобран.")
    return redirect("dashboard:knowledge")


@login_required
@staff_required
@require_POST
def knowledge_rebuild(request):
    result = rebuild_index()
    if result["ok"]:
        messages.success(request, f"Индекс собран: {result['chunks']} фрагментов.")
    else:
        messages.error(request, result["error"])
    return redirect("dashboard:knowledge")


@login_required
@staff_required
def questions_page(request):
    qs = QuestionLog.objects.select_related("user")
    q = request.GET.get("q", "").strip()
    language = request.GET.get("language", "").strip()
    unanswered = request.GET.get("unanswered") == "1"

    if q:
        qs = qs.filter(Q(question__icontains=q) | Q(answer__icontains=q))
    if language:
        qs = qs.filter(language=language)
    if unanswered:
        qs = qs.filter(is_unanswered=True)

    return render(
        request,
        "dashboard/questions.html",
        {
            "questions": qs[:300],
            "q": q,
            "language": language,
            "unanswered": unanswered,
            "total": qs.count(),
        },
    )


@login_required
@staff_required
def questions_export(request):
    qs = QuestionLog.objects.select_related("user").order_by("-created_at")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="questions.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Дата", "Пользователь", "Язык", "Без ответа", "Вопрос", "Ответ"])
    for item in qs:
        writer.writerow(
            [
                timezone.localtime(item.created_at).strftime("%Y-%m-%d %H:%M"),
                str(item.user) if item.user else "",
                "Қазақша" if item.language == "kk" else "Русский",
                "да" if item.is_unanswered else "нет",
                item.question,
                item.answer,
            ]
        )
    return response
