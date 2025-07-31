# SupportGrove.Online

A mental health support community platform that allows users to anonymously share lived experiences and advice to help others through recovery from addiction, abuse, trauma, displacement, mental health issues, and more.

## 🌟 Features

- **Anonymous Story Sharing** with guided recovery questions
- **Six Support Categories**: Addiction Recovery, Trauma & Healing, Mental Health, Life Transitions, Relationship Recovery, Self-Care & Wellness
- **Interactive Community**: Comments, reactions (hearts, hugs, sparkles), and conversation threading
- **Story Forwarding**: Share meaningful conversations via email or shareable links
- **Notification System**: Stay connected with community interactions
- **Mobile Responsive**: Optimized for all devices
- **Calming Design**: Grove Green theme designed for mental health support

## 🚀 Quick Deploy

### Railway (Recommended - $5/month)
1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Deploy backend from `/backend` folder
4. Deploy frontend from `/frontend` folder
5. Configure custom domain

### Render (Free tier available)
1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create web service from `/backend`
4. Create static site from `/frontend`
5. Configure environment variables

## 🛠️ Local Development

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Environment Variables

### Backend
- `FLASK_ENV=development` (for local) or `production`
- `SECRET_KEY=your-secret-key`
- `DATABASE_URL=sqlite:///app.db` (default)

### Frontend
- `VITE_API_BASE_URL=http://localhost:5000/api` (for local)

## 📱 Tech Stack

- **Backend**: Flask, SQLAlchemy, SQLite
- **Frontend**: React, Vite, Tailwind CSS, Radix UI
- **Deployment**: Railway, Render, Vercel, Docker

## 🤝 Contributing

This platform is designed to support mental health communities. Contributions that enhance accessibility, safety, and user experience are welcome.

## 📄 License

MIT License - Feel free to use this platform to support your community.

## 🆘 Crisis Resources

If you're in crisis, please reach out:
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/

---

**SupportGrove.Online** - Building bridges of support, one story at a time. 🌱

