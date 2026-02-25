# Contributing to TanStack POS

First off, thank you for considering contributing to TanStack POS! 🎉

This project exists because of contributors like you. Whether you're fixing a typo, reporting a bug, or building a new feature, your contribution matters.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#-reporting-bugs)
  - [Suggesting Features](#-suggesting-features)
  - [Submitting Code](#-submitting-code)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

---

## Code of Conduct

This project follows a simple code of conduct:

- **Be respectful** — Treat everyone with respect. No harassment, discrimination, or toxic behavior.
- **Be constructive** — Focus on improving the project. Critique ideas, not people.
- **Be patient** — Maintainers are volunteers. Response times may vary.
- **Be inclusive** — Welcome newcomers and help them get started.

---

## Getting Started

Before you start contributing, please:

1. **Read the [README](README.md)** to understand the project
2. **Check existing [Issues](../../issues)** to avoid duplicates
3. **Set up your local environment** (see [Development Setup](#development-setup))

---

## How to Contribute

### 🐛 Reporting Bugs

Found a bug? Help us fix it!

**Before submitting:**
- Check if the issue already exists
- Try to reproduce it on the latest version
- Gather relevant information

**When submitting, include:**

```markdown
**Bug Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Browser: [e.g., Chrome 120, Firefox 121]
- Node.js version: [e.g., 20.10.0]
- Docker version: [e.g., 24.0.7]
```

### 💡 Suggesting Features

Have an idea to make TanStack POS better?

**Before submitting:**
- Check if it's already been suggested
- Consider if it fits the project scope (restaurant POS)
- Think about implementation complexity

**When submitting, include:**

```markdown
**Feature Description**
A clear description of what you want.

**Problem It Solves**
What problem does this solve? Who benefits?

**Proposed Solution**
How do you envision this working?

**Alternatives Considered**
Other approaches you've thought about.

**Additional Context**
Mockups, examples from other software, etc.
```

### 🔧 Submitting Code

Ready to write some code? Awesome!

**Good first contributions:**
- Documentation improvements
- Bug fixes with clear reproduction steps
- Test coverage improvements
- Accessibility improvements
- Performance optimizations

**Before you start:**
1. Comment on the issue you want to work on (or create one)
2. Wait for maintainer confirmation to avoid duplicate work
3. Fork the repository and create a feature branch

---

## Development Setup

### Prerequisites

- Node.js 20+ 
- Docker & Docker Compose
- Git
- A code editor (VS Code recommended)

### Local Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/tan-pos.git
cd tan-pos

# 2. Install dependencies
npm install

# 3. Start the database
docker-compose up -d postgres

# 4. Run database migrations (if applicable)
npm run db:push

# 5. Start the development server
npm run dev

# 6. Open http://localhost:3000
```

### Project Structure

```
src/
├── components/       # Reusable UI components
├── routes/           # Page components (file-based routing)
│   └── dashboard/    # Protected dashboard routes
├── integrations/     # tRPC setup and API routes
│   └── trpc/
│       ├── router.ts # All tRPC procedures
│       └── react.ts  # React Query integration
├── db/               # Database schema and utilities
│   ├── schema.ts     # Drizzle ORM schema
│   └── index.ts      # Database connection
├── lib/              # Shared utilities
│   └── auth-context.tsx
└── hooks/            # Custom React hooks
```

### Useful Commands

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
npm run format       # Format with Prettier
npm run typecheck    # TypeScript type checking
docker-compose up    # Start all services
docker-compose down  # Stop all services
```

---

## Code Style

We use automated tools to maintain consistency:

- **ESLint** — JavaScript/TypeScript linting
- **Prettier** — Code formatting
- **TypeScript** — Static type checking

### Guidelines

```typescript
// ✅ Good: Descriptive names, proper typing
const calculateOrderTotal = (items: OrderItem[]): number => {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0)
}

// ❌ Bad: Vague names, any types
const calc = (x: any) => {
  return x.reduce((a: any, b: any) => a + b.price * b.qty, 0)
}
```

### File Naming

- **Components:** PascalCase (`OrderCard.tsx`)
- **Utilities:** camelCase (`formatCurrency.ts`)
- **Routes:** kebab-case (`dashboard/kitchen.tsx`)
- **Types:** PascalCase (`types/Order.ts`)

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change, no new feature or fix |
| `perf` | Performance improvement |
| `test` | Adding tests |
| `chore` | Build process, dependencies |

### Examples

```bash
feat(kitchen): add food/beverage filter toggle
fix(payment): resolve table status not updating after payment
docs(readme): update installation instructions
refactor(orders): simplify order status calculation
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows the style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No console.log or debugging code
- [ ] All tests pass (if applicable)
- [ ] Documentation updated (if needed)

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Closes #(issue number)

## Screenshots
If UI changes, add before/after screenshots.

## Testing
How did you test these changes?

## Checklist
- [ ] My code follows the project style
- [ ] I have tested my changes
- [ ] I have updated documentation
```

### Review Process

1. **Submit PR** against `main` branch
2. **Automated checks** run (lint, types, build)
3. **Maintainer review** within 1-7 days
4. **Address feedback** if requested
5. **Merge** once approved

---

## Community

### Getting Help

- **GitHub Issues** — Bug reports and feature requests
- **GitHub Discussions** — Questions and ideas
- **Website** — [kadekdodik.my.id](https://kadekdodik.my.id)

### Recognition

All contributors are recognized in:
- GitHub's contributor graph
- Release notes for significant contributions
- Special thanks in documentation

---

## Thank You! 🙏

Every contribution, no matter how small, helps make TanStack POS better for restaurants around the world. We appreciate your time and effort!

Happy coding! 🚀
