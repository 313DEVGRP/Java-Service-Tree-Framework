/**
 * Session persistence - save quiz history to ~/.claude-quiz/
 */

import { mkdir, writeFile, readFile, readdir } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';

const QUIZ_DIR = join(homedir(), '.claude-quiz');
const SESSIONS_DIR = join(QUIZ_DIR, 'sessions');
const STATS_FILE = join(QUIZ_DIR, 'stats.json');

/**
 * Ensure quiz directories exist
 */
async function ensureDirs() {
  try {
    await mkdir(QUIZ_DIR, { recursive: true });
    await mkdir(SESSIONS_DIR, { recursive: true });
  } catch (err) {
    // Ignore if already exists
  }
}

/**
 * Generate session ID from current timestamp
 */
function generateSessionId() {
  const now = new Date();
  const date = now.toISOString().split('T')[0];
  const time = now.toTimeString().split(' ')[0].replace(/:/g, '');
  return `${date}_${time}`;
}

/**
 * Save quiz session to file
 */
export async function saveSession(results) {
  try {
    await ensureDirs();

    const sessionId = generateSessionId();
    const sessionData = {
      session_id: sessionId,
      profile: results.profile,
      topics: results.topics,
      questions_total: results.totalQuestions,
      questions_correct: results.correctCount,
      questions_skipped: results.skippedCount,
      percentage: results.questions.filter(q => !q.skipped).length > 0
        ? Math.round((results.correctCount / results.questions.filter(q => !q.skipped).length) * 100)
        : 0,
      duration_seconds: Math.round((results.endTime - results.startTime) / 1000),
      by_category: results.byCategory,
      wrong_questions: results.questions
        .filter(q => !q.correct && !q.skipped)
        .map(q => ({
          id: q.question.id,
          category: q.question.category,
          category_id: q.question.category_id,
          question: q.question.question,
          user_answer: q.userAnswer,
          correct_answer: q.question.correct,
          doc_reference: q.question.doc_reference
        })),
      timestamp: new Date().toISOString()
    };

    // Save session file
    const sessionFile = join(SESSIONS_DIR, `${sessionId}.json`);
    await writeFile(sessionFile, JSON.stringify(sessionData, null, 2));

    // Update aggregate stats
    await updateStats(sessionData);

    return sessionId;
  } catch (err) {
    // Silent fail - don't break quiz if persistence fails
    console.error('Warning: Could not save session:', err.message);
    return null;
  }
}

/**
 * Update aggregate statistics
 */
async function updateStats(sessionData) {
  let stats = {
    total_sessions: 0,
    total_questions: 0,
    total_correct: 0,
    by_category: {},
    by_profile: {},
    last_session: null
  };

  // Load existing stats
  try {
    const existing = await readFile(STATS_FILE, 'utf-8');
    stats = JSON.parse(existing);
  } catch {
    // File doesn't exist yet
  }

  // Update totals
  stats.total_sessions++;
  stats.total_questions += sessionData.questions_total;
  stats.total_correct += sessionData.questions_correct;
  stats.last_session = sessionData.timestamp;

  // Update by category
  for (const [categoryId, categoryStats] of Object.entries(sessionData.by_category)) {
    if (!stats.by_category[categoryId]) {
      stats.by_category[categoryId] = { name: categoryStats.name, correct: 0, total: 0 };
    }
    stats.by_category[categoryId].correct += categoryStats.correct;
    stats.by_category[categoryId].total += categoryStats.total;
  }

  // Update by profile
  if (!stats.by_profile[sessionData.profile]) {
    stats.by_profile[sessionData.profile] = { sessions: 0, correct: 0, total: 0 };
  }
  stats.by_profile[sessionData.profile].sessions++;
  stats.by_profile[sessionData.profile].correct += sessionData.questions_correct;
  stats.by_profile[sessionData.profile].total += sessionData.questions_total;

  // Save updated stats
  await writeFile(STATS_FILE, JSON.stringify(stats, null, 2));
}

/**
 * Load previous session (for retry)
 */
export async function loadSession(sessionId) {
  try {
    const sessionFile = join(SESSIONS_DIR, `${sessionId}.json`);
    const content = await readFile(sessionFile, 'utf-8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * List recent sessions
 */
export async function listSessions(limit = 10) {
  try {
    await ensureDirs();
    const files = await readdir(SESSIONS_DIR);
    const jsonFiles = files.filter(f => f.endsWith('.json')).sort().reverse();
    return jsonFiles.slice(0, limit).map(f => f.replace('.json', ''));
  } catch {
    return [];
  }
}

/**
 * Get aggregate stats
 */
export async function getStats() {
  try {
    const content = await readFile(STATS_FILE, 'utf-8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}
