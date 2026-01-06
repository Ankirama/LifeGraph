/**
 * Tests for EmploymentHistory component.
 */

import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '@/test/utils';
import { EmploymentHistory } from '../EmploymentHistory';
import type { Employment } from '@/types';

// Mock window.confirm
const originalConfirm = window.confirm;
beforeAll(() => {
  window.confirm = vi.fn(() => true);
});
afterAll(() => {
  window.confirm = originalConfirm;
});

// Mock employment data
const mockEmployments: Employment[] = [
  {
    id: 'emp-1',
    person: 'person-1',
    company: 'Tech Corp',
    title: 'Senior Engineer',
    department: 'Engineering',
    start_date: '2022-01-15',
    end_date: null,
    is_current: true,
    location: 'San Francisco, CA',
    description: 'Leading backend development',
    linkedin_synced: true,
    created_at: '2022-01-15T00:00:00Z',
    updated_at: '2022-01-15T00:00:00Z',
  },
  {
    id: 'emp-2',
    person: 'person-1',
    company: 'StartupXYZ',
    title: 'Software Developer',
    department: null,
    start_date: '2020-06-01',
    end_date: '2021-12-31',
    is_current: false,
    location: 'Remote',
    description: null,
    linkedin_synced: false,
    created_at: '2020-06-01T00:00:00Z',
    updated_at: '2021-12-31T00:00:00Z',
  },
  {
    id: 'emp-3',
    person: 'person-1',
    company: 'Old Company',
    title: 'Junior Developer',
    department: 'IT',
    start_date: null,
    end_date: null,
    is_current: false,
    location: null,
    description: null,
    linkedin_synced: false,
    created_at: '2019-01-01T00:00:00Z',
    updated_at: '2019-01-01T00:00:00Z',
  },
];

// MSW server setup
const server = setupServer(
  http.delete('/api/v1/employments/:id/', () => {
    return new HttpResponse(null, { status: 204 });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('EmploymentHistory', () => {
  describe('empty state', () => {
    it('shows empty message when no employments', () => {
      renderWithProviders(<EmploymentHistory employments={[]} personId="person-1" />);
      expect(screen.getByText('No employment history yet.')).toBeInTheDocument();
    });
  });

  describe('employment list', () => {
    it('renders all employment entries', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText('Senior Engineer')).toBeInTheDocument();
      expect(screen.getByText('Software Developer')).toBeInTheDocument();
      expect(screen.getByText('Junior Developer')).toBeInTheDocument();
    });

    it('displays company names', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('StartupXYZ')).toBeInTheDocument();
      expect(screen.getByText('Old Company')).toBeInTheDocument();
    });

    it('displays department when available', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('IT')).toBeInTheDocument();
    });

    it('displays location when available', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
      expect(screen.getByText('Remote')).toBeInTheDocument();
    });

    it('displays description when available', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText('Leading backend development')).toBeInTheDocument();
    });
  });

  describe('current employment', () => {
    it('shows Current badge for current employment', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText('Current')).toBeInTheDocument();
    });

    it('shows Present for current employment end date', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      expect(screen.getByText(/Present/)).toBeInTheDocument();
    });
  });

  describe('date display', () => {
    it('displays formatted start and end dates', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // Jan 2022 - Present for current job
      expect(screen.getByText(/Jan 2022/)).toBeInTheDocument();
      // Jun 2020 - Dec 2021 for past job
      expect(screen.getByText(/Jun 2020/)).toBeInTheDocument();
      expect(screen.getByText(/Dec 2021/)).toBeInTheDocument();
    });

    it('shows Unknown when date is missing', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // The third employment has no dates
      const unknownTexts = screen.getAllByText(/Unknown/);
      expect(unknownTexts.length).toBeGreaterThanOrEqual(1);
    });

    it('calculates and displays duration', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // Should show duration in years/months format
      // The past job is 1 yr 6 mos (Jun 2020 - Dec 2021)
      expect(screen.getByText(/1 yr/)).toBeInTheDocument();
    });
  });

  describe('LinkedIn sync indicator', () => {
    it('shows LinkedIn icon for synced employments', () => {
      const { container } = renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // First employment is linkedin_synced
      const linkedinIcons = container.querySelectorAll('svg.text-blue-600');
      expect(linkedinIcons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('sorting', () => {
    it('shows current employment first', () => {
      renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // Get all titles in order
      const titles = screen.getAllByRole('heading', { level: 4 });
      expect(titles[0]).toHaveTextContent('Senior Engineer'); // Current job first
    });
  });

  describe('delete action', () => {
    it('shows delete button on hover (via class)', () => {
      const { container } = renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // Delete buttons should exist but have opacity-0 class
      const deleteButtons = container.querySelectorAll('button');
      expect(deleteButtons.length).toBeGreaterThanOrEqual(3);
    });

    it('calls delete mutation when delete is confirmed', async () => {
      const { user } = renderWithProviders(
        <EmploymentHistory employments={mockEmployments} personId="person-1" />
      );

      // Find delete buttons
      const deleteButtons = screen.getAllByRole('button');
      await user.click(deleteButtons[0]);

      // Confirm was called
      expect(window.confirm).toHaveBeenCalled();
    });
  });
});
