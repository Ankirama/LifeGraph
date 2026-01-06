/**
 * Tests for ChatPage page.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { ChatPage } from '../ChatPage';

// Mock scrollIntoView which is not available in jsdom
Element.prototype.scrollIntoView = vi.fn();

// Mock data
const mockChatResponse = {
  answer: 'Based on your contacts, John Smith has a birthday on March 15th.',
};

// MSW server setup
const server = setupServer(
  http.post('/api/v1/ai/chat/', () => {
    return HttpResponse.json(mockChatResponse);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('ChatPage', () => {
  describe('page header', () => {
    it('displays page title', () => {
      renderWithProviders(<ChatPage />);
      expect(screen.getByText('AI Chat')).toBeInTheDocument();
    });

    it('displays page description', () => {
      renderWithProviders(<ChatPage />);
      expect(
        screen.getByText(/Ask questions about your contacts, relationships, and memories/i)
      ).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('displays welcome message when no messages', () => {
      renderWithProviders(<ChatPage />);
      expect(screen.getByText('Ask me anything')).toBeInTheDocument();
    });

    it('displays helpful description', () => {
      renderWithProviders(<ChatPage />);
      expect(
        screen.getByText(/I have access to all your contacts/i)
      ).toBeInTheDocument();
    });

    it('displays example questions', () => {
      renderWithProviders(<ChatPage />);
      expect(screen.getByText("When is my mother's birthday?")).toBeInTheDocument();
      expect(screen.getByText('Who works at Google?')).toBeInTheDocument();
      expect(screen.getByText('Tell me about my friends')).toBeInTheDocument();
    });
  });

  describe('chat input', () => {
    it('renders chat input field', () => {
      renderWithProviders(<ChatPage />);
      expect(screen.getByPlaceholderText('Ask about your contacts...')).toBeInTheDocument();
    });

    it('renders send button', () => {
      renderWithProviders(<ChatPage />);
      // The send button is the submit button in the form
      const submitButton = screen.getByRole('button', { name: '' }); // Send button has no text, just icon
      expect(submitButton).toBeInTheDocument();
    });

    it('disables send button when input is empty', () => {
      renderWithProviders(<ChatPage />);
      // Find the submit button (it's disabled when empty, so we can find it by that state)
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.getAttribute('type') === 'submit');
      expect(submitButton).toBeDisabled();
    });

    it('enables send button when input has text', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello');

      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.getAttribute('type') === 'submit');
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('example questions', () => {
    it('populates input when example is clicked', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      await user.click(screen.getByText("When is my mother's birthday?"));

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      expect(input).toHaveValue("When is my mother's birthday?");
    });
  });

  describe('chat functionality', () => {
    it('sends message when submit button is clicked', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Who has a birthday soon?');

      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.getAttribute('type') === 'submit');
      await user.click(submitButton!);

      await waitFor(() => {
        expect(screen.getByText('Who has a birthday soon?')).toBeInTheDocument();
      });
    });

    it('sends message when Enter is pressed', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Who has a birthday soon?{enter}');

      await waitFor(() => {
        expect(screen.getByText('Who has a birthday soon?')).toBeInTheDocument();
      });
    });

    it('clears input after sending message', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Who has a birthday soon?{enter}');

      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });

    it('displays user message in chat', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Tell me about John{enter}');

      await waitFor(() => {
        expect(screen.getByText('Tell me about John')).toBeInTheDocument();
      });
    });

    it('displays AI response in chat', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Tell me about John{enter}');

      await waitFor(() => {
        expect(
          screen.getByText(/Based on your contacts, John Smith has a birthday/i)
        ).toBeInTheDocument();
      });
    });

    it('shows loading indicator while waiting for response', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Tell me about John');

      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.getAttribute('type') === 'submit');
      await user.click(submitButton!);

      // Loading state briefly appears
      expect(screen.getByText('Tell me about John')).toBeInTheDocument();
    });
  });

  describe('clear chat', () => {
    it('shows clear chat button when messages exist', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello{enter}');

      await waitFor(() => {
        expect(screen.getByText(/Clear chat/i)).toBeInTheDocument();
      });
    });

    it('does not show clear chat button when no messages', () => {
      renderWithProviders(<ChatPage />);
      expect(screen.queryByText(/Clear chat/i)).not.toBeInTheDocument();
    });

    it('clears messages when clear chat is clicked', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello{enter}');

      await waitFor(() => {
        expect(screen.getByText('Hello')).toBeInTheDocument();
      });

      await user.click(screen.getByText(/Clear chat/i));

      await waitFor(() => {
        expect(screen.queryByText('Hello')).not.toBeInTheDocument();
        expect(screen.getByText('Ask me anything')).toBeInTheDocument();
      });
    });
  });

  describe('error handling', () => {
    it('shows error message on API failure', async () => {
      server.use(
        http.post('/api/v1/ai/chat/', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello{enter}');

      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/i)).toBeInTheDocument();
      });
    });
  });

  describe('message display', () => {
    it('displays user messages aligned right', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello{enter}');

      await waitFor(() => {
        const userMessage = screen.getByText('Hello').closest('div');
        expect(userMessage?.parentElement?.className).toContain('justify-end');
      });
    });

    it('displays AI messages aligned left', async () => {
      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello{enter}');

      await waitFor(() => {
        const aiResponse = screen
          .getByText(/Based on your contacts/i)
          .closest('div');
        expect(aiResponse?.parentElement?.className).toContain('justify-start');
      });
    });
  });

  describe('input behavior', () => {
    it('disables input while loading', async () => {
      // Create a delayed response
      server.use(
        http.post('/api/v1/ai/chat/', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json(mockChatResponse);
        })
      );

      const { user } = renderWithProviders(<ChatPage />);

      const input = screen.getByPlaceholderText('Ask about your contacts...');
      await user.type(input, 'Hello');

      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.getAttribute('type') === 'submit');
      await user.click(submitButton!);

      // Input should be disabled during loading
      expect(input).toBeDisabled();

      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
    });
  });
});
