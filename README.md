# Simple-WebAuthn-Passkey-Authentication-Demo

# Simple WebAuthn Passkey Authentication Demo

A minimal yet functional implementation of passwordless authentication using WebAuthn/FIDO2 passkeys. This project demonstrates how modern browsers enable secure, phishing-resistant authentication through public-key cryptography, eliminating the need for traditional passwords.

The system includes a Python-based backend and a modern frontend built with Node.js (SolidJS/Vue), covering the full authentication lifecycle: user registration (credential creation) and login (assertion verification). It is designed to be lightweight, easy to understand, and practical for developers exploring passkey-based authentication.

This repository can serve as a learning resource, a reference implementation, or a starting point for integrating passkey authentication into real-world applications.

---

## 🚀 Features

- 🔐 Implements passwordless authentication using WebAuthn/FIDO2 passkeys  
- 🌐 Demonstrates secure registration and login flows with public-key cryptography  
- ⚙️ Lightweight and easy-to-understand example for learning and experimentation  

---

## 🧱 Tech Stack

- **Backend:** Python  
- **Frontend:** Node.js (SolidJS / Vue)  
- **Database:** PostgreSQL  
- **Cache:** Redis  
- **Auth Standard:** WebAuthn / FIDO2  

---

## 🛠️ Getting Started

### 1. Start Database & Cache (Docker)

Run PostgreSQL:

```bash
docker run --name chat-auth \
  -e POSTGRES_USER=chat_user \
  -e POSTGRES_PASSWORD=chat_pass \
  -e POSTGRES_DB=chat_auth \
  -p 5432:5432 \
  -d postgres:16

```

Run Redis

```bash
docker run --name chat-redis \
  -p 6379:6379 \
  -d redis:7
```

### 2. Run the server (backend)

```bash
cd backend

uv run python -m app.main
```

### 2. Run the browser client (frontend)

```bash
cd frontend

npm run dev
```

## 🔐 Authentication Flow

This project demonstrates the two main WebAuthn ceremonies:

- **Registration**
  - User creates a passkey (credential)
  - Public key is stored on the server

- **Authentication**
  - User signs a challenge using their passkey
  - Server verifies the signature using the stored public key

---

## 📝 Notes

- Tested using passkeys stored with the Bitwarden Firefox extension  
- Uses PostgreSQL for persistent storage and Redis for caching/session handling  
- Focused on clarity and simplicity rather than production-ready hardening  

---

## 📌 Purpose

This project is intended for:

- Learning how WebAuthn / passkeys work in practice  
- Exploring passwordless authentication systems  
- Serving as a base for more advanced implementations  

---

## 📄 License

AGPL 3.0