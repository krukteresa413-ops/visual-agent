import { describe, expect, it } from 'vitest';
import { actionBarAnchor } from './actionBarAnchor';

describe('actionBarAnchor', () => {
  it('anchors above the selected node using React Flow viewport transform', () => {
    expect(actionBarAnchor({ x: 100, y: 80, width: 240, height: 160 }, { x: 20, y: 10, zoom: 2 })).toEqual({
      left: 460,
      top: 124,
    });
  });

  it('keeps the bar inside the top viewport padding', () => {
    expect(actionBarAnchor({ x: 10, y: 0, width: 100, height: 80 }, { x: 0, y: 0, zoom: 1 })).toEqual({
      left: 60,
      top: 8,
    });
  });
});
