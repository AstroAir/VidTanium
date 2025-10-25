# VidTanium GUI Design System - Testing Guide

## Overview

This guide provides comprehensive testing procedures for the redesigned VidTanium GUI, which uses the Unified Design System. All tests should verify consistency, visual correctness, and theme support.

## Testing Environment Setup

### Prerequisites
- Python 3.11+
- PySide6 and qfluentwidgets installed
- `pytest` and `pytest-qt` for automated testing
- Both light and dark theme configurations available

### Running the Application

```bash
# Standard GUI launch
python main.py

# With debug logging
python main.py --debug

# Specify config directory
python main.py --config "/path/to/config"
```

## Visual Testing Checklist

### Color System Verification

#### Light Theme Colors
- [ ] Primary button (#0078D4) appears correct
- [ ] Surface background (#FFFFFF) is clean white
- [ ] Surface container (#F5F5F5) is light gray
- [ ] Text color (#1F1F1F) has good contrast
- [ ] Secondary text (#616161) is readable but subdued
- [ ] Borders (#E0E0E0) are subtle but visible
- [ ] Success color (#107C10) appears for positive actions
- [ ] Warning color (#CA5010) appears for warnings
- [ ] Error color (#D13438) appears for errors
- [ ] No gradients visible anywhere in the interface

#### Dark Theme Colors
- [ ] Primary button (#4CC2FF) appears correct
- [ ] Surface background (#1E1E1E) is properly dark
- [ ] Surface container (#2D2D2D) is slightly elevated
- [ ] Text color (#FFFFFF) has good contrast
- [ ] Secondary text (#C8C8C8) is visible
- [ ] Borders (#484848) are distinguishable
- [ ] Success color (#6CCB5F) appears for positive actions
- [ ] Warning color (#F7630C) appears for warnings
- [ ] Error color (#F1707B) appears for errors
- [ ] No gradients visible anywhere in the interface

### Component Testing

#### Buttons
- [ ] Primary buttons use primary color background
- [ ] Secondary buttons use surface container with outline
- [ ] Text buttons are transparent with hover effect
- [ ] Button text is white on primary (light theme)
- [ ] Button hover states are clearly visible
- [ ] Disabled buttons appear grayed out
- [ ] Button padding is consistent (8px 16px)
- [ ] Border radius is 4px
- [ ] No gradients on button backgrounds

#### Cards
- [ ] Card background matches surface color
- [ ] Card borders are 1px outline color
- [ ] Card border radius is 8px
- [ ] Card padding is 16px
- [ ] Elevated cards show subtle shadow (Level 2)
- [ ] Interactive cards show hover effect
- [ ] No gradients on card backgrounds
- [ ] Text contrast is maintained on cards

#### Input Fields
- [ ] Input background is surface container
- [ ] Input border is 1px outline
- [ ] Input border radius is 4px
- [ ] Input padding is 8px 16px
- [ ] Focus state shows 2px primary border
- [ ] Placeholder text is visible but subdued
- [ ] Text cursor color is appropriate
- [ ] No gradients on input backgrounds

#### Status Badges
- [ ] Success badge uses success color
- [ ] Error badge uses error color
- [ ] Warning badge uses warning color
- [ ] Info badge uses primary color
- [ ] Badge padding is consistent
- [ ] Badge text is readable
- [ ] Badge corners are slightly rounded
- [ ] No gradients visible

#### Typography
- [ ] Display text (28px, 600 weight) appears large and bold
- [ ] Headline text (22px, 600 weight) is clear for sections
- [ ] Title text (16px, 600 weight) is used for card titles
- [ ] Body text (13px, 400 weight) is readable and normal weight
- [ ] Label text (13px, 500 weight) appears in form labels
- [ ] Caption text (11px, 400 weight) is small and readable
- [ ] Font hierarchy is clear and distinguishable
- [ ] Text rendering is smooth

#### Spacing and Layout
- [ ] XS spacing (4px) used appropriately
- [ ] SM spacing (8px) between related items
- [ ] MD spacing (16px) for standard padding
- [ ] LG spacing (24px) for large sections
- [ ] Spacing is consistent throughout
- [ ] Layout aligns to 8px grid
- [ ] No arbitrary padding values

#### Shadows and Elevation
- [ ] Level 2 shadow is subtle and present
- [ ] Shadows are smooth and realistic
- [ ] Elevated elements have appropriate depth
- [ ] No harsh or dark shadows
- [ ] Shadow opacity is consistent

### Theme Switching

#### Theme Toggle Functionality
- [ ] Light theme can be activated from settings
- [ ] Dark theme can be activated from settings
- [ ] Theme changes apply immediately
- [ ] All components update correctly
- [ ] Colors change appropriately
- [ ] No components remain in wrong theme

#### Theme Persistence
- [ ] Selected theme persists after restart
- [ ] Theme setting is saved to config
- [ ] Default theme is set correctly
- [ ] No theme reset on launch

### Design System Consistency

#### Component Style Consistency
- [ ] All primary buttons have same styling
- [ ] All secondary buttons have same styling
- [ ] All cards use consistent styling
- [ ] All inputs use consistent styling
- [ ] All badges use consistent colors
- [ ] All text uses appropriate typography

#### Color Consistency
- [ ] Primary color used only for CTAs (Call-To-Action)
- [ ] Semantic colors used appropriately
- [ ] No custom/undefined colors
- [ ] All colors come from design system

#### Spacing Consistency
- [ ] No custom padding values
- [ ] All spacing from DS.spacing()
- [ ] Margins align to grid
- [ ] Consistent padding in similar components

#### Typography Consistency
- [ ] Font sizes match design system
- [ ] Font weights match design system
- [ ] Font families are consistent
- [ ] Line heights are appropriate

### Navigation and Layout

#### Main Window
- [ ] Window title is displayed correctly
- [ ] Menu bar styling is consistent
- [ ] Navigation elements are clearly visible
- [ ] Layout is responsive
- [ ] No text overflow or clipping

#### Sidebar/Navigation
- [ ] Navigation items have proper spacing
- [ ] Active state is clearly indicated
- [ ] Hover effects work correctly
- [ ] Icons (if used) are properly colored
- [ ] Text is readable

#### Tabs
- [ ] Active tab is highlighted with primary color
- [ ] Inactive tabs use secondary styling
- [ ] Tab switching is smooth
- [ ] Content updates correctly
- [ ] Tab text is readable

#### Dialogs
- [ ] Dialog background is surface color
- [ ] Dialog title uses headline typography
- [ ] Dialog buttons use proper styling
- [ ] Dialog shadows are appropriate
- [ ] Content is properly centered/aligned

### Accessibility

#### Contrast Ratios
- [ ] Text color on surface has sufficient contrast
- [ ] Text color on primary has sufficient contrast
- [ ] All status indicators are distinguishable
- [ ] Focus indicators are visible

#### Visibility
- [ ] All UI elements are visible in light theme
- [ ] All UI elements are visible in dark theme
- [ ] No text is cut off or hidden
- [ ] Icons are clear and distinct
- [ ] Disabled states are visually different

### Responsive Design

#### Different Screen Sizes
- [ ] Layout adapts to smaller screens
- [ ] Components don't overlap
- [ ] Text remains readable
- [ ] Buttons remain clickable
- [ ] No horizontal scroll needed (typical sizes)

#### Different DPI Settings
- [ ] UI elements scale appropriately
- [ ] Text remains readable at different scales
- [ ] Spacing adapts proportionally
- [ ] Icons are sharp and clear

## Automated Testing

### Running Test Suite

```bash
# Run all GUI tests
pytest tests/gui/ -v

# Run design system tests
pytest tests/gui/test_design_system.py -v

# Run theme tests
pytest tests/gui/test_theme_system.py -v

# Run with coverage
pytest tests/gui/ --cov=src/gui --cov-report=html
```

### Test Categories

#### Color Tests
```python
# tests/gui/test_design_system_colors.py
def test_light_theme_colors():
    """Verify all light theme colors are correct."""

def test_dark_theme_colors():
    """Verify all dark theme colors are correct."""

def test_color_theme_switching():
    """Verify colors change when switching themes."""
```

#### Component Tests
```python
# tests/gui/test_components.py
def test_button_styling():
    """Verify button applies correct styles."""

def test_card_styling():
    """Verify card applies correct styles."""

def test_input_styling():
    """Verify input applies correct styles."""
```

#### Typography Tests
```python
# tests/gui/test_typography.py
def test_typography_styles():
    """Verify typography CSS is correct."""

def test_font_sizes():
    """Verify font sizes match spec."""
```

#### Spacing Tests
```python
# tests/gui/test_spacing.py
def test_spacing_values():
    """Verify spacing values are correct."""

def test_padding_consistency():
    """Verify padding is consistent."""
```

## Manual Testing Procedures

### Test Case 1: Light Theme Verification

**Steps:**
1. Launch application
2. Set theme to Light in settings
3. Navigate through all main screens
4. Check each component type

**Expected Results:**
- All colors match light theme specification
- Text has good contrast
- No gradients visible
- Consistent spacing throughout

**Pass/Fail:** _____

### Test Case 2: Dark Theme Verification

**Steps:**
1. Launch application
2. Set theme to Dark in settings
3. Navigate through all main screens
4. Check each component type

**Expected Results:**
- All colors match dark theme specification
- Text has good contrast on dark background
- No gradients visible
- Consistent spacing throughout

**Pass/Fail:** _____

### Test Case 3: Theme Switching

**Steps:**
1. Launch application with Light theme
2. Switch to Dark theme
3. Verify all components update
4. Switch back to Light theme
5. Verify all components update

**Expected Results:**
- Colors change immediately
- All components update correctly
- No elements remain in wrong theme

**Pass/Fail:** _____

### Test Case 4: Button Consistency

**Steps:**
1. Navigate to all screens with buttons
2. Compare primary buttons
3. Compare secondary buttons
4. Compare text buttons

**Expected Results:**
- All primary buttons have identical styling
- All secondary buttons have identical styling
- All text buttons have identical styling
- Hover/focus states are consistent

**Pass/Fail:** _____

### Test Case 5: Card Consistency

**Steps:**
1. Navigate to screens with cards
2. Compare card styling
3. Check elevated cards
4. Check interactive cards

**Expected Results:**
- All cards use consistent border/background
- Shadows are consistent
- Elevated cards show same elevation
- Interactive effects are consistent

**Pass/Fail:** _____

### Test Case 6: Typography Hierarchy

**Steps:**
1. Navigate through all screens
2. Identify each typography level
3. Compare with specification

**Expected Results:**
- Display text is largest and boldest
- Headline text is clearly different from body
- Title text distinguishes cards
- Body text is most common
- Caption text is smallest
- Clear visual hierarchy

**Pass/Fail:** _____

### Test Case 7: Spacing Grid

**Steps:**
1. Use browser dev tools or design inspection tool
2. Measure padding/margins
3. Compare to 8px grid values

**Expected Results:**
- Padding values: 8, 16, 24, 32, 48, 64px
- Margins values: 8, 16, 24, 32, 48, 64px
- No arbitrary values like 12px, 20px, etc.
- Consistent spacing throughout

**Pass/Fail:** _____

### Test Case 8: No Gradients

**Steps:**
1. Inspect CSS of all components
2. Search for "gradient" keywords
3. Check all background colors

**Expected Results:**
- No `qlineargradient` in stylesheets
- No `radial gradient` anywhere
- All backgrounds are solid colors
- Clean, professional appearance

**Pass/Fail:** _____

### Test Case 9: Accessibility Contrast

**Steps:**
1. Use accessibility inspector tool
2. Check text on all background colors
3. Verify color contrast ratios

**Expected Results:**
- All regular text >= 4.5:1 contrast ratio
- All large text >= 3:1 contrast ratio
- Status indicators are distinguishable
- Focus indicators are visible

**Pass/Fail:** _____

### Test Case 10: Component Interaction

**Steps:**
1. Hover over buttons
2. Click buttons
3. Focus on inputs
4. Tab through navigation
5. Toggle states

**Expected Results:**
- Hover states are clearly visible
- Focus states show proper indicator
- Disabled states are obvious
- Interactions are responsive
- No visual lag

**Pass/Fail:** _____

## Known Issues and Migration Notes

### Gradient Removal
- **Issue**: Previously used gradients have been removed
- **Status**: Complete
- **Impact**: Components may look different but are more professional
- **Resolution**: All gradients replaced with solid colors from design system

### Theme System Changes
- **Issue**: Old gradient-based theme system replaced with unified system
- **Status**: Complete
- **Impact**: Consistent theme switching
- **Resolution**: Use UnifiedDesignSystem for all styling

### Color Values
- **Issue**: Some components may have outdated color references
- **Status**: Verify with checklist
- **Impact**: Inconsistent appearance
- **Resolution**: Update to use DS.color() method

## Design Inconsistency Reporting

### How to Report

1. **Identify the Issue**
   - Component affected
   - Light or dark theme
   - Expected vs actual appearance

2. **Document the Issue**
   - Take screenshot showing problem
   - Note the component type
   - Describe the inconsistency
   - Provide reproduction steps

3. **Submit Report**
   - Create issue in GitHub with title: `[Design] Component Name - Issue`
   - Attach screenshot
   - Include checklist items affected
   - Reference this testing guide

### Report Template

```
## Design Inconsistency Report

**Component**: [Name of component]
**Theme**: Light / Dark
**Issue**: [Description of inconsistency]

**Expected**: [What should appear]
**Actual**: [What actually appears]

**Screenshots**: [Attach images]

**Affected Items**:
- [ ] Color system
- [ ] Spacing
- [ ] Typography
- [ ] Shadows
- [ ] Borders
- [ ] Other: ___

**Reproduction Steps**:
1. ...
2. ...
3. ...
```

## Testing Screenshots Directory

Store all screenshots used for testing in:
```
d:\Project\VidTanium\docs\screenshots\
  ├── light-theme/
  │   ├── main-window.png
  │   ├── components.png
  │   ├── buttons.png
  │   ├── cards.png
  │   └── dialogs.png
  └── dark-theme/
      ├── main-window.png
      ├── components.png
      ├── buttons.png
      ├── cards.png
      └── dialogs.png
```

## Quick Reference Checklist

For quick testing without full guide:

```
Visual Quality
- [ ] No gradients anywhere
- [ ] All colors from design system
- [ ] Consistent spacing (8px grid)
- [ ] Clear visual hierarchy
- [ ] Professional appearance

Light Theme
- [ ] Primary color is #0078D4
- [ ] Surface is white
- [ ] Text is dark and readable
- [ ] Borders are subtle

Dark Theme
- [ ] Primary color is #4CC2FF
- [ ] Surface is dark (#1E1E1E)
- [ ] Text is light and readable
- [ ] Borders are visible

Theme Switching
- [ ] Theme switches smoothly
- [ ] All components update
- [ ] No elements in wrong theme
- [ ] Setting persists

Components
- [ ] Buttons styled consistently
- [ ] Cards have uniform appearance
- [ ] Inputs are uniform
- [ ] Badges use semantic colors
- [ ] All text uses typography system

Interaction
- [ ] Hover effects work
- [ ] Focus states visible
- [ ] Disabled states obvious
- [ ] No visual lag
- [ ] Responsive to user input
```

## Related Documentation

- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md) - Complete design system specification
- [CODE_EXAMPLES.md](./CODE_EXAMPLES.md) - Code examples for implementation
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migrating to new design system
- [DESIGN_PATTERNS.md](./DESIGN_PATTERNS.md) - Common UI patterns

## Next Steps

1. Run manual tests from this guide
2. Execute automated test suite
3. Document any inconsistencies
4. Update components as needed
5. Re-test after changes
6. Verify theme persistence
7. Check accessibility compliance
