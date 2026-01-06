import os
import re
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from github import Github
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
CLIENT_SECRET = os.environ["GITHUB_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8000/callback"
AUTHORIZED_OWNERS = os.environ.get("AUTHORIZED_OWNERS")
if AUTHORIZED_OWNERS is not None:
    AUTHORIZED_OWNERS = [o.lower() for o in AUTHORIZED_OWNERS.split(",")]


class CustomAsyncClient(httpx.AsyncClient):
    def delete_with_payload(self, **kwargs):
        return self.request(method="DELETE", **kwargs)


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# État global simplifié
state = {
    "token": None,
    "repos_by_owner": {},
    "owners": [],
    "members": [],
}


@app.get("/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        token = resp.json().get("access_token")
        state["token"] = token

        g = Github(token)
        user = g.get_user()

        all_repos = user.get_repos()
        repos_by_owner = {}

        for r in all_repos:
            owner = r.owner.login
            if owner not in repos_by_owner:
                repos_by_owner[owner] = []
            repos_by_owner[owner].append(r.full_name)

        state["repos_by_owner"] = repos_by_owner
        state["owners"] = sorted(list(repos_by_owner.keys()))
        
        if AUTHORIZED_OWNERS is not None:
            state["owners"] = [owner for owner in state["owners"] if owner.lower() in AUTHORIZED_OWNERS]
            state["repos_by_owner"] = {owner: repos_by_owner[owner] for owner in state["owners"]}
    return RedirectResponse(url="/")


def parse_command(command: str):
    patterns = {
        "repo": r"#repo:([\w\d\-\_.\/]+)",
        "label": r"#label:([\w\d\-\_.\/]+)",
        "assignee": r"#assignee:([\w\d\-\_.]+)",
        # "status": r"#status:([\w\d\-\_.]+)",
    }

    return {
        "repo": re.search(patterns["repo"], command).group(1)
        if re.search(patterns["repo"], command)
        else "",
        "label": re.search(patterns["label"], command).group(1)
        if re.search(patterns["label"], command)
        else "",
        "assignee": re.search(patterns["assignee"], command).group(1)
        if re.search(patterns["assignee"], command)
        # else "",
        # "status": re.search(patterns["status"], command).group(1)
        # if re.search(patterns["status"], command)
        else "",
        "title": re.sub(r'#\w+(:("[^"]+"|\S+))?', "", command).strip(),
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "state": state,
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
        },
    )

@app.get("/logout")
async def logout():
    """Déconnecte l'utilisateur et révoque le token OAuth auprès de GitHub."""
    if state["token"]:
        async with httpx.AsyncClient() as client:
            # L'URL de révocation pour les OAuth Apps
            # Elle nécessite l'ID de l'application dans l'URL
            url = f"https://api.github.com/applications/{CLIENT_ID}/grant"
            
            try:
                # GitHub demande une authentification Basic avec Client ID et Secret
                # pour autoriser la révocation d'un token
                response = await client.request(
                    method="DELETE",
                    url=url,
                    auth=(CLIENT_ID, CLIENT_SECRET),
                    json={"access_token": state["token"]}
                )
                
                if response.status_code == 204:
                    print("Token révoqué avec succès auprès de GitHub.")
                else:
                    print(f"Échec de la révocation : {response.status_code}")
                    
            except Exception as e:
                print(f"Erreur lors de la communication avec GitHub : {e}")

    # Nettoyage de l'état local même si la révocation API échoue
    state["token"] = None
    state["repos_by_owner"] = {}
    state["owners"] = []
    
    # Redirection vers la page d'accueil (qui affichera le bouton de connexion)
    return RedirectResponse(url="/")

@app.get("/parse")
async def parse_api(cmd: str):
    return parse_command(cmd)


@app.post("/create")
async def create_api(request: Request):
    data = await request.json()
    parsed = parse_command(data["command"])
    if not state["token"]:
        return {"success": False, "message": "Session expirée"}

    try:
        g = Github(state["token"])
        repo = g.get_repo(parsed["repo"])

        # Trouver le milestone si un status est spécifié
        # milestone = None
        # if parsed["status"]:
        #     ms = repo.get_milestones(state="open")
        #     for m in ms:
        #         if m.title.lower() == parsed["status"].lower():
        #             milestone = m
        #             break

        issue_data = dict(
            title=parsed["title"],
            body=data.get("description", ""),
            labels=[parsed["label"]] if parsed["label"] else [],
            assignees=[parsed["assignee"]] if parsed["assignee"] else [],
            # milestone=milestone,
            )
            
        print(issue_data)
        issue = repo.create_issue(
            **issue_data
        )
        print("Success")
        return {
            "success": True,
            "message": f"Issue #{issue.number} créée avec succès !",
        }
    except Exception as e:
        print("Failure")
        print(e)
        return {"success": False, "message": f"Erreur : {str(e)}"}


@app.get("/repo-details")
async def get_repo_details(full_name: str):
    if not state["token"]:
        return {"success": False}
    try:
        g = Github(state["token"])
        repo = g.get_repo(full_name)
        return {
            "success": True,
            "labels": [label.name for label in repo.get_labels()],
            "assignees": [a.login for a in repo.get_assignees()],
            "milestones": [m.title for m in repo.get_milestones(state="open")],
        }
    except Exception:
        return {"success": False}


