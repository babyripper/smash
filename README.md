# FitTracker - App per Tracciamento Dieta e Allenamento

Un'applicazione completa per tracciare dieta, allenamenti e peso con sistema di ruoli avanzato per nutrizionisti e personal trainer.

## 🚀 Features

- 📄 **Caricamento PDF**: Dieta e schede allenamento
- 📋 **Diario Pasti**: Registrazione quotidiana con emozioni e idratazione
- 💪 **Allenamenti**: Tracciamento workout con dettagli muscolari
- ⚖️ **Peso**: Grafico andamento nel tempo
- 🔐 **Sistema Ruoli**: Admin, Utente, Nutrizionista, Personal Trainer
- 📊 **Dashboard**: Panoramica completa dei progressi
- 🛒 **SaaS Ready**: Architettura scalabile per multi-utente

## 🛠️ Stack Tecnologico

### Backend
- **FastAPI** - Framework web moderno e performante
- **PostgreSQL** - Database relazionale
- **SQLAlchemy** - ORM per Python
- **JWT** - Autenticazione token-based
- **Python 3.11+**

### Frontend
- **React** - UI moderna e reattiva
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Chart.js** - Grafici per andamento peso

### Deployment
- **Docker** - Containerizzazione
- **Docker Compose** - Orchestrazione locale

## 📁 Struttura Progetto

```
fittracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routes/
│   │   ├── auth/
│   │   ├── permissions/
│   │   └── database.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .gitignore
```

## 🔧 Setup Locale

### Prerequisiti
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Docker (opzionale)

### Installazione Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Installazione Frontend

```bash
cd frontend
npm install
```

### Variabili d'Ambiente

Crea `.env` nella cartella backend:

```
DATABASE_URL=postgresql://user:password@localhost/fittracker
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Avvio con Docker Compose

```bash
docker-compose up -d
```

L'app sarà disponibile a `http://localhost:3000`

## 📚 API Endpoints (Principali)

### Auth
- `POST /api/auth/register` - Registrazione
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token

### Utenti
- `GET /api/users/me` - Profilo corrente
- `PUT /api/users/me` - Aggiorna profilo
- `POST /api/users/invite-professional` - Invita nutrizionista/trainer

### Diete
- `POST /api/diete/upload` - Carica PDF dieta
- `GET /api/diete` - Visualizza dieta
- `GET /api/diete/my-diets` - Diete caricate da me

### Diario Pasti
- `POST /api/diario-pasti` - Nuovo pasto
- `GET /api/diario-pasti` - Elenco pasti
- `PUT /api/diario-pasti/{id}` - Modifica pasto

### Allenamenti
- `POST /api/allenamenti/upload-scheda` - Carica scheda
- `POST /api/allenamenti` - Registra allenamento
- `GET /api/allenamenti` - Elenco allenamenti

### Peso
- `POST /api/peso` - Registra peso
- `GET /api/peso` - Storico peso
- `GET /api/peso/grafico` - Dati per grafico

## 🔐 Sistema Ruoli

| Ruolo | Dieta | Scheda | Diario Pasti | Peso | Admin |
|-------|-------|--------|--------------|------|-------|
| Admin | ✅ Tutto | ✅ Tutto | ✅ Tutto | ✅ Tutto | ✅ |
| Utente | 📖 Leggi | 📖 Leggi | ✅ Scrivi | ✅ Traccia | ❌ |
| Nutrizionista | ✅ Carica | ❌ | 📖 Leggi | 📖 Leggi | ❌ |
| Personal Trainer | ❌ | ✅ Carica | ❌ | 📖 Leggi | ❌ |

## 🗄️ Database Schema

Vedi `backend/app/models/` per tutti i modelli.

### Principali Entità
- **Users** - Utenti del sistema
- **Diete** - PDF delle diete
- **SchadeAllenamento** - PDF schede
- **DiarioPasti** - Registrazione pasti
- **Allenamenti** - Registrazione workout
- **TracciamentoPeso** - Storico peso
- **UserRelationships** - Connessioni nutrizionista/trainer

## 📊 Roadmap

- [ ] Fase 1: Backend base con autenticazione
- [ ] Fase 2: API endpoints dieta e allenamenti
- [ ] Fase 3: Frontend React base
- [ ] Fase 4: Sistema notifiche
- [ ] Fase 5: Integrazione pagamenti (Stripe)
- [ ] Fase 6: Mobile app (React Native)

## 📄 Licenza

MIT

## 👤 Autore

babyripper

---

**Inizio: 28 Maggio 2026**
