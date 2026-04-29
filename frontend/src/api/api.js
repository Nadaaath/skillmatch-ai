const API_URL = "/api";

async function handleResponse(res) {
  const text = await res.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: text };
    }
  }

  if (!res.ok) {
    throw new Error(data.detail || data.error || res.statusText);
  }

  return data;
}

export async function uploadCandidateCv({
  fullName,
  email,
  experienceYears,
  file,
}) {
  const formData = new FormData();
  formData.append("full_name", fullName);
  formData.append("email", email);
  formData.append("experience_years", String(experienceYears));
  formData.append("file", file);

  const res = await fetch(`${API_URL}/candidates/upload-cv`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(res);
}

export async function createJob({ title, requiredSkills }) {
  const url = new URL(
    `${API_URL}/jobs/create`,
    window.location.origin
  );
  url.searchParams.set("title", title);
  url.searchParams.set("required_skills", requiredSkills);

  const res = await fetch(url, {
    method: "POST",
  });

  return handleResponse(res);
}

export async function matchJob({ candidateId, jobId }) {
  const url = new URL(
    `${API_URL}/jobs/match`,
    window.location.origin
  );
  url.searchParams.set("candidate_id", String(candidateId));
  url.searchParams.set("job_id", String(jobId));

  const res = await fetch(url, {
    method: "GET",
  });

  return handleResponse(res);
}
