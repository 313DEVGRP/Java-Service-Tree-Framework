/**
 * User prompts using inquirer
 */

import inquirer from 'inquirer';
import chalk from 'chalk';

export async function selectProfile(profiles) {
  const { profile } = await inquirer.prompt([
    {
      type: 'list',
      name: 'profile',
      message: 'Select your profile:',
      choices: Object.entries(profiles).map(([key, value]) => ({
        name: `${value.name} (${value.description})`,
        value: key
      }))
    }
  ]);
  return profile;
}

export async function selectTopics(topics, defaultTopics) {
  const { topicChoice } = await inquirer.prompt([
    {
      type: 'list',
      name: 'topicChoice',
      message: 'Select topics to quiz:',
      choices: [
        { name: chalk.green('All topics (recommended)'), value: 'all' },
        { name: 'Profile defaults', value: 'defaults' },
        { name: 'Custom selection...', value: 'custom' }
      ]
    }
  ]);

  if (topicChoice === 'all') {
    return Object.keys(topics).map(Number);
  }

  if (topicChoice === 'defaults') {
    return defaultTopics;
  }

  // Custom selection
  const { selectedTopics } = await inquirer.prompt([
    {
      type: 'checkbox',
      name: 'selectedTopics',
      message: 'Select topics (space to toggle, enter to confirm):',
      choices: Object.entries(topics).map(([id, name]) => ({
        name: `[${id}] ${name}`,
        value: parseInt(id),
        checked: defaultTopics.includes(parseInt(id))
      })),
      validate: (answer) => {
        if (answer.length === 0) {
          return 'You must select at least one topic.';
        }
        return true;
      }
    }
  ]);

  return selectedTopics;
}

export async function promptAnswer() {
  const { answer } = await inquirer.prompt([
    {
      type: 'list',
      name: 'answer',
      message: 'Your answer:',
      choices: [
        { name: 'A', value: 'a' },
        { name: 'B', value: 'b' },
        { name: 'C', value: 'c' },
        { name: 'D', value: 'd' },
        new inquirer.Separator(),
        { name: chalk.gray('Skip question'), value: 'skip' },
        { name: chalk.gray('Quit quiz'), value: 'quit' }
      ]
    }
  ]);
  return answer;
}

export async function promptContinue() {
  const { cont } = await inquirer.prompt([
    {
      type: 'confirm',
      name: 'cont',
      message: 'Continue to next question?',
      default: true
    }
  ]);
  return cont;
}

export async function promptRetry() {
  const { retry } = await inquirer.prompt([
    {
      type: 'list',
      name: 'retry',
      message: 'What would you like to do?',
      choices: [
        { name: 'Retry wrong questions only', value: 'retry-wrong' },
        { name: 'New quiz (different questions)', value: 'new-quiz' },
        { name: 'Exit', value: 'exit' }
      ]
    }
  ]);
  return retry;
}
