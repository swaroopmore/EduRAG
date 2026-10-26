/* Which subject is the learner working in? Shared by every subject-scoped page. */
import { Api } from "./api.js";
import { queryParam } from "./utils.js";

const ID_KEY = "current_subject_id"; // same keys as the previous frontend
const NAME_KEY = "current_subject_name";

export function storedSubjectId() {
  try {
    return localStorage.getItem(ID_KEY);
  } catch {
    return null;
  }
}

export function rememberSubject(subject) {
  try {
    if (subject) {
      localStorage.setItem(ID_KEY, subject.id);
      localStorage.setItem(NAME_KEY, subject.name);
    } else {
      localStorage.removeItem(ID_KEY);
      localStorage.removeItem(NAME_KEY);
    }
  } catch {
    /* ignore */
  }
}

/** URL ?subject=… wins, then the remembered subject, then the most recently created one. */
export function pickSubject(subjects) {
  if (!subjects.length) return null;
  const wanted = queryParam("subject") || storedSubjectId();
  return subjects.find((s) => s.id === wanted) || subjects[0];
}

export async function loadSubjects() {
  const subjects = await Api.subjects();
  return Array.isArray(subjects) ? subjects : [];
}
