# NotebookLM Frontend Features Test Plan

## Overview
This document outlines a comprehensive test plan for all frontend features and flows in the NotebookLM application.

## Test Environment
- **Frontend URL**: http://localhost:8081
- **Backend API**: http://localhost:5003
- **Test User**: test@example.com / password123

## Core Features & Flows to Test

### 1. Authentication Flow
- [ ] **Login Page Display**
  - Landing page with NotebookLM branding
  - Feature highlights (Document Processing, AI Chat, Audio Podcasts)
  - Login form with email/password fields
  - Demo credentials displayed
  - Sign In / Sign Up tabs

- [ ] **Login Process**
  - Email input validation
  - Password input (masked)
  - Successful login with valid credentials
  - Error handling for invalid credentials
  - Redirect to dashboard after login

- [ ] **Token Management**
  - JWT token storage
  - Token verification on page load
  - Auto-logout on token expiry
  - Session persistence

### 2. Dashboard Features
- [ ] **Dashboard Layout**
  - Header with NotebookLM logo and user info
  - Statistics cards (Notebooks, Sources, Conversations, Podcasts)
  - Search bar for notebooks
  - New Notebook button

- [ ] **Notebook Management**
  - Display notebook list
  - Notebook cards with title, description, stats
  - Create new notebook modal
  - Notebook creation form validation
  - Success notifications
  - Real-time counter updates

- [ ] **Navigation**
  - Sign out functionality
  - Search notebooks functionality
  - Responsive design elements

### 3. Notebook Detail View
- [ ] **Navigation & Layout**
  - Notebook header with title and description
  - Tab navigation (Sources, Chat, Content, Podcasts, Search)
  - Back to Dashboard button
  - User info display

- [ ] **Sources Tab**
  - File upload interface (drag & drop)
  - Supported file formats display
  - Document list with count
  - Upload progress indicators
  - File management (view, delete)

- [ ] **Chat Tab**
  - Conversation list
  - New chat creation
  - Chat interface with message history
  - AI response with source citations
  - Real-time typing indicators

- [ ] **Content Tab**
  - Content generation options:
    - Summary generation
    - FAQ creation
    - Timeline creation
    - Study guide generation
    - Briefing creation
  - Generated content display
  - Export/download options

- [ ] **Podcasts Tab**
  - Podcast format selection:
    - Conversational (2 hosts)
    - Interview format
    - Narrative style
    - Educational format
  - Voice selection (male/female)
  - Podcast generation progress
  - Audio player controls
  - Podcast list management

- [ ] **Search Tab**
  - Semantic search interface
  - Search suggestions
  - Query examples
  - Search results with relevance scoring
  - Source attribution
  - Search history

### 4. API Integration
- [ ] **Authentication APIs**
  - POST /api/auth/login
  - GET /api/auth/verify
  - Token refresh handling

- [ ] **Notebook APIs**
  - GET /api/notebooks (list)
  - POST /api/notebooks (create)
  - GET /api/notebooks/:id (detail)
  - PUT /api/notebooks/:id (update)
  - DELETE /api/notebooks/:id (delete)

- [ ] **Document APIs**
  - POST /api/notebooks/:id/sources (upload)
  - GET /api/notebooks/:id/sources (list)
  - DELETE /api/sources/:id (delete)

- [ ] **Chat APIs**
  - POST /api/notebooks/:id/chat (send message)
  - GET /api/notebooks/:id/chats (list conversations)

- [ ] **Content APIs**
  - POST /api/notebooks/:id/content (generate)
  - GET /api/notebooks/:id/content (list)

- [ ] **Podcast APIs**
  - POST /api/notebooks/:id/podcasts (create)
  - GET /api/notebooks/:id/podcasts (list)

- [ ] **Search APIs**
  - POST /api/notebooks/:id/search (semantic search)

### 5. Error Handling
- [ ] **Network Errors**
  - Connection timeout handling
  - Server error responses (500, 503)
  - Retry mechanisms

- [ ] **Validation Errors**
  - Form validation messages
  - File upload errors
  - Input sanitization

- [ ] **User Experience**
  - Loading states and spinners
  - Error notifications
  - Success confirmations
  - Progress indicators

### 6. Responsive Design
- [ ] **Desktop Layout**
  - Full-width dashboard
  - Multi-column layouts
  - Hover effects and interactions

- [ ] **Mobile Layout**
  - Responsive navigation
  - Touch-friendly buttons
  - Mobile-optimized forms
  - Swipe gestures

### 7. Performance
- [ ] **Loading Times**
  - Initial page load
  - API response times
  - File upload performance
  - Search response times

- [ ] **Optimization**
  - Code splitting
  - Asset compression
  - Caching strategies
  - Bundle size optimization

## Test Execution Priority

### Phase 1: Core Functionality (Critical)
1. Authentication flow
2. Dashboard display
3. Notebook creation
4. Notebook detail view
5. Basic navigation

### Phase 2: Feature Testing (High Priority)
1. File upload (Sources tab)
2. Chat functionality
3. Content generation
4. Search functionality

### Phase 3: Advanced Features (Medium Priority)
1. Podcast generation
2. Advanced search
3. Content export
4. User preferences

### Phase 4: Polish & Performance (Low Priority)
1. Responsive design testing
2. Performance optimization
3. Error handling edge cases
4. Accessibility testing

## Success Criteria
- All core flows work without errors
- API integration is stable and reliable
- User interface is intuitive and responsive
- Error handling provides clear feedback
- Performance meets acceptable standards

## Test Data Requirements
- Test user account with valid credentials
- Sample documents for upload testing
- Various file formats (PDF, DOCX, TXT, etc.)
- Test content for AI processing

## Known Issues to Verify
1. Notebook list synchronization between sessions
2. Token expiry handling
3. File upload progress tracking
4. Real-time updates for counters
5. CORS configuration for API calls

