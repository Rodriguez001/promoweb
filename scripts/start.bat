@echo off
setlocal enabledelayedexpansion

REM PromoWeb Africa - Script de démarrage pour Windows
REM Lance l'application complète avec Docker Compose

echo 🚀 Démarrage de PromoWeb Africa...

REM Vérifier que Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas installé. Veuillez l'installer d'abord.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord.
    pause
    exit /b 1
)

REM Vérifier que le fichier .env existe
if not exist .env (
    echo 📋 Création du fichier .env à partir du template...
    copy .env.example .env
    echo ⚠️  Veuillez configurer les variables d'environnement dans .env
    echo 📝 Notamment: DATABASE_PASSWORD, JWT_SECRET_KEY, STRIPE_SECRET_KEY
)

REM Créer les répertoires nécessaires
echo 📁 Création des répertoires...
if not exist uploads mkdir uploads
if not exist logs mkdir logs
if not exist database\backups mkdir database\backups

REM Nettoyer les containers existants si nécessaire
echo 🧹 Nettoyage des containers existants...
docker-compose down --remove-orphans

REM Construire et lancer les services
echo 🏗️  Construction des images Docker...
docker-compose build --no-cache

echo 🚀 Lancement des services...
docker-compose up -d

REM Attendre que la base de données soit prête
echo ⏳ Attente de la base de données...
timeout /t 15 /nobreak >nul

REM Lancer les migrations
echo 🗄️  Application des migrations...
docker-compose exec backend alembic upgrade head

REM Créer un utilisateur admin par défaut
echo 👤 Création de l'utilisateur admin par défaut...
docker-compose exec backend python -c "from app.core.database import get_db_context; from app.services.auth import auth_service; from app.schemas.user import UserCreate; import asyncio; async def create_admin(): [try: admin_data = UserCreate(email='admin@promoweb.cm', password='Admin123!', confirm_password='Admin123!', first_name='Admin', last_name='PromoWeb'); user = await auth_service.create_user(admin_data); async with get_db_context() as db: user.role = 'admin'; await db.commit(); print('✅ Utilisateur admin créé: admin@promoweb.cm / Admin123!'); except Exception as e: print(f'ℹ️  Utilisateur admin existe déjà ou erreur: {e}')]; asyncio.run(create_admin())"

REM Afficher les URLs d'accès
echo.
echo 🎉 PromoWeb Africa est maintenant en cours d'exécution!
echo.
echo 📱 URLs d'accès:
echo    Frontend:          http://localhost:3000
echo    API Backend:       http://localhost:8000
echo    Documentation API: http://localhost:8000/docs
echo    pgAdmin:          http://localhost:5050
echo    Redis Commander:   http://localhost:8081
echo.
echo 👤 Compte admin par défaut:
echo    Email: admin@promoweb.cm
echo    Mot de passe: Admin123!
echo.
echo 📋 Commandes utiles:
echo    Voir les logs:        docker-compose logs -f
echo    Arrêter l'application: docker-compose down
echo    Redémarrer:           docker-compose restart
echo.
echo 📚 Documentation complète: README.md

REM Vérifier que tous les services sont en cours d'exécution
timeout /t 5 /nobreak >nul
echo 🔍 Vérification des services...
docker-compose ps

echo.
echo Appuyez sur une touche pour continuer...
pause >nul
