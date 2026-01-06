import { Page, APIRequestContext } from '@playwright/test';

/**
 * Test data for E2E tests
 */
export const testData = {
  persons: {
    john: {
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      nickname: 'Johnny',
      birthday: '1990-05-15',
      primary_email: 'john.doe@example.com',
      primary_phone: '+1234567890',
      met_context: 'Work conference',
      notes: 'Great colleague from tech conference',
    },
    jane: {
      first_name: 'Jane',
      last_name: 'Smith',
      full_name: 'Jane Smith',
      birthday: '1985-08-20',
      primary_email: 'jane.smith@example.com',
      met_context: 'College friend',
    },
  },
  tags: {
    friend: { name: 'Friend', color: '#10B981' },
    work: { name: 'Work', color: '#3B82F6' },
    family: { name: 'Family', color: '#EF4444' },
  },
  groups: {
    college: { name: 'College', color: '#8B5CF6' },
    company: { name: 'Company', color: '#F59E0B' },
  },
  anecdotes: {
    memory: {
      title: 'Great dinner party',
      content: 'We had an amazing dinner party last summer with lots of laughter.',
      anecdote_type: 'memory',
      date: '2023-06-15',
      location: 'San Francisco',
    },
    note: {
      title: 'Work preferences',
      content: 'Prefers morning meetings, coffee drinker, vegetarian.',
      anecdote_type: 'note',
    },
  },
  relationshipTypes: {
    friend: { name: 'Friend', inverse_name: 'Friend', is_asymmetric: false },
    colleague: { name: 'Colleague', inverse_name: 'Colleague', is_asymmetric: false },
    parent: { name: 'Parent', inverse_name: 'Child', is_asymmetric: true },
  },
};

/**
 * API helper class for test data management
 */
export class TestDataHelper {
  constructor(private request: APIRequestContext, private baseUrl: string = '/api/v1') {}

  /**
   * Create a person via API
   */
  async createPerson(data: Partial<typeof testData.persons.john>) {
    const response = await this.request.post(`${this.baseUrl}/persons/`, {
      data,
    });
    return response.json();
  }

  /**
   * Create a tag via API
   */
  async createTag(data: { name: string; color?: string }) {
    const response = await this.request.post(`${this.baseUrl}/tags/`, {
      data,
    });
    return response.json();
  }

  /**
   * Create a relationship via API
   */
  async createRelationship(data: {
    person_a: string;
    person_b: string;
    relationship_type: string;
  }) {
    const response = await this.request.post(`${this.baseUrl}/relationships/`, {
      data,
    });
    return response.json();
  }

  /**
   * Create an anecdote via API
   */
  async createAnecdote(personId: string, data: Partial<typeof testData.anecdotes.memory>) {
    const response = await this.request.post(`${this.baseUrl}/anecdotes/`, {
      data: {
        ...data,
        persons: [personId],
      },
    });
    return response.json();
  }

  /**
   * Delete a person via API
   */
  async deletePerson(id: string) {
    await this.request.delete(`${this.baseUrl}/persons/${id}/`);
  }

  /**
   * Clean up test data
   */
  async cleanupTestData() {
    // Get all persons with test email patterns
    const response = await this.request.get(`${this.baseUrl}/persons/`);
    const data = await response.json();

    for (const person of data.results || []) {
      if (
        person.primary_email?.includes('@example.com') ||
        person.first_name === 'E2E'
      ) {
        await this.deletePerson(person.id);
      }
    }
  }
}

/**
 * UI helper class for common interactions
 */
export class UIHelper {
  constructor(private page: Page) {}

  /**
   * Navigate to a page and wait for load
   */
  async navigateTo(path: string) {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Fill a form field by label
   */
  async fillField(label: string, value: string) {
    await this.page.getByLabel(label).fill(value);
  }

  /**
   * Click a button by name
   */
  async clickButton(name: string | RegExp) {
    await this.page.getByRole('button', { name }).click();
  }

  /**
   * Wait for toast/notification message
   */
  async waitForToast(message: string | RegExp) {
    await this.page.getByText(message).waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * Close modal if open
   */
  async closeModal() {
    const closeButton = this.page.getByRole('button', { name: /close|cancel|×/i });
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  }

  /**
   * Get list item count
   */
  async getListItemCount(listSelector: string = '[data-testid="person-card"]') {
    const items = await this.page.$$(listSelector);
    return items.length;
  }
}

/**
 * Create test data helper from page context
 */
export function createTestHelper(page: Page) {
  return {
    data: new TestDataHelper(page.request()),
    ui: new UIHelper(page),
  };
}
