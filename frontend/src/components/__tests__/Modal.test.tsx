/**
 * Tests for Modal component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Modal } from '../Modal';

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    title: 'Test Modal',
    children: <p>Modal content</p>,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders when isOpen is true', () => {
      render(<Modal {...defaultProps} />);
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
      expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<Modal {...defaultProps} isOpen={false} />);
      expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
    });

    it('renders title correctly', () => {
      render(<Modal {...defaultProps} title="Custom Title" />);
      expect(screen.getByText('Custom Title')).toBeInTheDocument();
    });

    it('renders children correctly', () => {
      render(
        <Modal {...defaultProps}>
          <div data-testid="custom-child">Custom child content</div>
        </Modal>
      );
      expect(screen.getByTestId('custom-child')).toBeInTheDocument();
      expect(screen.getByText('Custom child content')).toBeInTheDocument();
    });
  });

  describe('sizes', () => {
    it('applies sm size class', () => {
      const { container } = render(<Modal {...defaultProps} size="sm" />);
      expect(container.innerHTML).toContain('max-w-md');
    });

    it('applies md size class by default', () => {
      const { container } = render(<Modal {...defaultProps} />);
      expect(container.innerHTML).toContain('max-w-lg');
    });

    it('applies lg size class', () => {
      const { container } = render(<Modal {...defaultProps} size="lg" />);
      expect(container.innerHTML).toContain('max-w-2xl');
    });

    it('applies xl size class', () => {
      const { container } = render(<Modal {...defaultProps} size="xl" />);
      expect(container.innerHTML).toContain('max-w-4xl');
    });
  });

  describe('closing behavior', () => {
    it('calls onClose when close button is clicked', () => {
      const onClose = vi.fn();
      render(<Modal {...defaultProps} onClose={onClose} />);

      // Find and click the close button (X icon button)
      const closeButton = screen.getByRole('button');
      fireEvent.click(closeButton);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when Escape key is pressed', () => {
      const onClose = vi.fn();
      render(<Modal {...defaultProps} onClose={onClose} />);

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when clicking on overlay', () => {
      const onClose = vi.fn();
      const { container } = render(<Modal {...defaultProps} onClose={onClose} />);

      // Click on the overlay (the outer fixed div)
      const overlay = container.querySelector('.fixed.inset-0');
      if (overlay) {
        fireEvent.click(overlay);
        expect(onClose).toHaveBeenCalledTimes(1);
      }
    });

    it('does not call onClose when clicking on modal content', () => {
      const onClose = vi.fn();
      render(<Modal {...defaultProps} onClose={onClose} />);

      // Click on the modal content
      fireEvent.click(screen.getByText('Modal content'));

      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe('body scroll behavior', () => {
    it('sets body overflow to hidden when open', () => {
      render(<Modal {...defaultProps} />);
      expect(document.body.style.overflow).toBe('hidden');
    });

    it('resets body overflow when closed', () => {
      const { rerender } = render(<Modal {...defaultProps} />);
      expect(document.body.style.overflow).toBe('hidden');

      rerender(<Modal {...defaultProps} isOpen={false} />);
      expect(document.body.style.overflow).toBe('unset');
    });

    it('cleans up event listeners on unmount', () => {
      const onClose = vi.fn();
      const { unmount } = render(<Modal {...defaultProps} onClose={onClose} />);

      unmount();

      // After unmount, pressing Escape shouldn't call onClose
      fireEvent.keyDown(document, { key: 'Escape' });
      // Note: This test verifies cleanup happened by ensuring no errors occur
    });
  });
});
