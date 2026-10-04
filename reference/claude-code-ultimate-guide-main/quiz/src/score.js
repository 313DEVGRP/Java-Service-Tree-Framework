/**
 * Score tracking and display
 */

import chalk from 'chalk';
import { displayCategoryScore } from './ui.js';
import { promptRetry } from './prompts.js';

/**
 * Display final score summary
 */
export function displayFinalScore(results, topics) {
  const { totalQuestions, correctCount, skippedCount, startTime, endTime, byCategory } = results;

  const answeredCount = results.questions.filter(q => !q.skipped).length;
  const percentage = answeredCount > 0 ? Math.round((correctCount / answeredCount) * 100) : 0;
  const duration = Math.round((endTime - startTime) / 1000);
  const minutes = Math.floor(duration / 60);
  const seconds = duration % 60;

  console.log(chalk.cyan('\n' + '='.repeat(60)));
  console.log(chalk.cyan.bold('   QUIZ COMPLETE'));
  console.log(chalk.cyan('='.repeat(60)));

  // Overall score
  let scoreColor = chalk.green;
  if (percentage < 50) scoreColor = chalk.red;
  else if (percentage < 75) scoreColor = chalk.yellow;

  console.log();
  console.log(chalk.white.bold('Overall Score: ') + scoreColor.bold(`${correctCount}/${answeredCount} (${percentage}%)`));

  if (skippedCount > 0) {
    console.log(chalk.gray(`Skipped: ${skippedCount} questions`));
  }

  // Category breakdown
  console.log();
  console.log(chalk.white.bold('By Category:'));

  const categoryScores = [];
  for (const [categoryId, stats] of Object.entries(byCategory)) {
    if (stats.total > 0) {
      const categoryName = stats.name || topics[categoryId] || `Category ${categoryId}`;
      console.log(displayCategoryScore(categoryName, stats.correct, stats.total));
      categoryScores.push({
        id: categoryId,
        name: categoryName,
        correct: stats.correct,
        total: stats.total,
        percentage: Math.round((stats.correct / stats.total) * 100)
      });
    }
  }

  // Weak areas (< 75%)
  const weakAreas = categoryScores.filter(c => c.percentage < 75);
  if (weakAreas.length > 0) {
    console.log();
    console.log(chalk.yellow.bold('Weak Areas (< 75%):'));
    for (const area of weakAreas) {
      console.log(chalk.yellow(`  - ${area.name}: Review section ${area.id} in the guide`));
    }
  }

  // Recommended reading
  if (weakAreas.length > 0) {
    console.log();
    console.log(chalk.blue.bold('Recommended Reading:'));
    for (const area of weakAreas.slice(0, 3)) {
      const anchor = getSectionAnchor(area.id);
      console.log(chalk.blue(`  ${area.id}. guide/ultimate-guide.md${anchor}`));
    }
  }

  // Time
  console.log();
  console.log(chalk.gray(`Time: ${minutes > 0 ? `${minutes} min ` : ''}${seconds} sec`));

  console.log(chalk.gray('\n' + '-'.repeat(60)));
}

/**
 * Get section anchor for documentation link
 */
function getSectionAnchor(categoryId) {
  const anchors = {
    1: '#1-quick-start-day-1',
    2: '#2-core-concepts',
    3: '#3-memory--settings',
    4: '#4-agents',
    5: '#5-skills',
    6: '#6-commands',
    7: '#7-hooks',
    8: '#8-mcp-servers',
    9: '#9-advanced-patterns',
    10: '#10-reference'
  };
  return anchors[categoryId] || '';
}

/**
 * Offer retry options after quiz
 */
export async function offerRetry(results) {
  const wrongCount = results.questions.filter(q => !q.correct && !q.skipped).length;

  if (wrongCount === 0) {
    console.log(chalk.green.bold('\nPerfect score! No questions to retry.'));
    return 'exit';
  }

  console.log(chalk.gray(`\nYou missed ${wrongCount} question${wrongCount > 1 ? 's' : ''}.`));

  return promptRetry();
}
