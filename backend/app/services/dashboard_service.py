from uuid import UUID

from app.models.document import DocumentStatus
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.dashboard import ActivityItem, DashboardResponse, SubjectProgress
from app.schemas.document import DocumentResponse


class DashboardService:
    def __init__(self, repository: DashboardRepository, subjects: SubjectRepository):
        self.repository = repository
        self.subjects = subjects

    def get_dashboard(self, user_id: UUID) -> DashboardResponse:
        repo = self.repository
        status_counts = repo.document_status_counts(user_id)
        attempts, average = repo.quiz_attempt_stats(user_id)

        return DashboardResponse(
            subjects=repo.count_subjects(user_id),
            documents=sum(status_counts.values()),
            flashcards=repo.count_flashcards(user_id),
            quizzes=repo.count_quizzes(user_id),
            notes=repo.count_notes(user_id),
            study_plans=repo.count_study_plans(user_id),
            storage_used=repo.storage_used(user_id),
            documents_ready=status_counts.get(DocumentStatus.READY, 0),
            documents_in_progress=sum(status_counts.get(s, 0) for s in DocumentStatus.IN_PROGRESS),
            documents_failed=status_counts.get(DocumentStatus.FAILED, 0),
            chat_messages=repo.count_chat_messages(user_id),
            quiz_attempts=attempts,
            average_quiz_accuracy=average,
            flashcards_mastered=repo.count_mastered_flashcards(user_id),
            study_sessions_completed=repo.count_completed_sessions(user_id),
            subject_progress=self._subject_progress(user_id),
            recent_documents=self._recent_documents(user_id),
            recent_activity=self._recent_activity(user_id),
        )

    # -------------------------------------------------------------- helpers
    def _recent_documents(self, user_id: UUID) -> list[DocumentResponse]:
        result = []
        for document, subject_name in self.repository.recent_documents(user_id):
            document.subject_name = subject_name
            result.append(DocumentResponse.model_validate(document))
        return result

    def _subject_progress(self, user_id: UUID) -> list[SubjectProgress]:
        repo = self.repository
        subjects = self.subjects.get_by_user(user_id)
        counts = self.subjects.counts_by_subject(user_id)
        mastered = repo.mastered_by_subject(user_id)
        completed = repo.completed_sessions_by_subject(user_id)
        attempts = repo.attempts_by_subject(user_id)
        latest = repo.latest_by_subject(user_id)

        items: list[SubjectProgress] = []
        for subject in subjects:
            c = counts.get(subject.id, {})
            flashcards = c.get("flashcards", 0)
            sessions = c.get("study_sessions", 0)
            attempt_count, best = attempts.get(subject.id, (0, None))

            # Progress = average of the learning signals that exist for the subject:
            # flashcards mastered, study sessions completed, best quiz score.
            signals: list[float] = []
            if flashcards:
                signals.append(mastered.get(subject.id, 0) / flashcards)
            if sessions:
                signals.append(completed.get(subject.id, 0) / sessions)
            if attempt_count and best is not None:
                signals.append(best / 100)
            progress = round(100 * sum(signals) / len(signals)) if signals else None

            items.append(
                SubjectProgress(
                    id=subject.id,
                    name=subject.name,
                    documents=c.get("documents", 0),
                    documents_ready=c.get("documents_ready", 0),
                    notes=c.get("notes", 0),
                    flashcards=flashcards,
                    flashcards_mastered=mastered.get(subject.id, 0),
                    quiz_questions=c.get("quiz_questions", 0),
                    quiz_attempts=attempt_count,
                    best_quiz_accuracy=best if attempt_count else None,
                    study_sessions=sessions,
                    study_sessions_completed=completed.get(subject.id, 0),
                    progress=progress,
                    last_activity=latest.get(subject.id) or subject.created_at,
                )
            )
        items.sort(key=lambda s: s.last_activity, reverse=True)
        return items

    def _recent_activity(self, user_id: UUID) -> list[ActivityItem]:
        repo = self.repository
        events: list[ActivityItem] = []

        for document, subject_name in repo.recent_documents(user_id):
            events.append(
                ActivityItem(
                    type="document",
                    title=f"Uploaded {document.original_filename}",
                    subject_id=document.subject_id,
                    subject_name=subject_name,
                    at=document.created_at,
                )
            )
        for question, subject_id, at, subject_name in repo.recent_chats(user_id):
            short = question if len(question) <= 80 else question[:77] + "…"
            events.append(
                ActivityItem(type="chat", title=f"Asked: {short}", subject_id=subject_id, subject_name=subject_name, at=at)
            )
        for score, total, subject_id, at, subject_name in repo.recent_attempts(user_id):
            events.append(
                ActivityItem(type="quiz", title=f"Scored {score}/{total} on a quiz", subject_id=subject_id, subject_name=subject_name, at=at)
            )
        labels = {
            "notes": "Generated {n} note sections",
            "flashcards": "Generated {n} flashcards",
            "quiz_generated": "Generated a {n}-question quiz",
            "plan": "Generated a {n}-day study plan",
        }
        for kind, subject_id, subject_name, n, at in repo.generated_resources(user_id):
            events.append(
                ActivityItem(type=kind, title=labels[kind].format(n=n), subject_id=subject_id, subject_name=subject_name, at=at)
            )

        events.sort(key=lambda e: e.at, reverse=True)
        return events[:10]
