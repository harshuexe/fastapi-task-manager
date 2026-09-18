from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import (
    Project, ProjectCreate, ProjectRead,
    Task, TaskCreate, TaskRead, TaskUpdate
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Task & Project Management API", lifespan=lifespan)


# ==========================================
# FULL WEB DASHBOARD UI (Tailwind CSS)
# ==========================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Task Manager Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen p-6">
        <div class="max-w-4xl mx-auto space-y-8">
            
            <!-- Header -->
            <header class="flex justify-between items-center border-b border-slate-800 pb-4">
                <div>
                    <h1 class="text-3xl font-bold text-indigo-400">⚡ Task & Project Manager</h1>
                    <p class="text-slate-400 text-sm">FastAPI + SQLModel + SQLite Powered</p>
                </div>
                <a href="/docs-modern" class="bg-slate-800 hover:bg-slate-700 text-xs px-3 py-2 rounded-lg border border-slate-700 text-slate-300">API Docs ↗</a>
            </header>

            <!-- Forms Grid -->
            <div class="grid md:grid-cols-2 gap-6">
                <!-- Add Project Form -->
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
                    <h2 class="text-lg font-semibold text-slate-200 mb-4">📁 Create New Project</h2>
                    <form id="projectForm" onsubmit="createProject(event)" class="space-y-3">
                        <input type="text" id="pTitle" placeholder="Project Title" required class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm focus:border-indigo-500 outline-none">
                        <input type="text" id="pDesc" placeholder="Description" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm focus:border-indigo-500 outline-none">
                        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg text-sm transition">Add Project</button>
                    </form>
                </div>

                <!-- Add Task Form -->
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
                    <h2 class="text-lg font-semibold text-slate-200 mb-4">✅ Create New Task</h2>
                    <form id="taskForm" onsubmit="createTask(event)" class="space-y-3">
                        <input type="text" id="tTitle" placeholder="Task Title" required class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm focus:border-indigo-500 outline-none">
                        <input type="text" id="tDesc" placeholder="Description" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm focus:border-indigo-500 outline-none">
                        <input type="number" id="tProjectId" placeholder="Project ID (e.g. 1)" required class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm focus:border-indigo-500 outline-none">
                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-lg text-sm transition">Add Task</button>
                    </form>
                </div>
            </div>

            <!-- Content Area -->
            <div class="space-y-6">
                <h2 class="text-xl font-bold text-slate-300">Your Projects & Tasks</h2>
                <div id="projectsList" class="space-y-4">Loading...</div>
            </div>
        </div>

        <script>
            const API = "";

            async function loadData() {
                const [pRes, tRes] = await Promise.all([
                    fetch('/projects/'),
                    fetch('/tasks/')
                ]);
                const projects = await pRes.json();
                const tasks = await tRes.json();

                const container = document.getElementById('projectsList');
                if (projects.length === 0) {
                    container.innerHTML = `<div class="text-slate-500 text-sm">No projects created yet. Create one above!</div>`;
                    return;
                }

                container.innerHTML = projects.map(p => {
                    const pTasks = tasks.filter(t => t.project_id === p.id);
                    return `
                        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div class="flex justify-between items-start mb-3">
                                <div>
                                    <span class="text-xs bg-indigo-950 text-indigo-400 font-mono px-2 py-0.5 rounded border border-indigo-800">ID: ${p.id}</span>
                                    <h3 class="text-lg font-bold text-white mt-1">${p.title}</h3>
                                    <p class="text-slate-400 text-sm">${p.description || ''}</p>
                                </div>
                            </div>
                            
                            <div class="mt-4 pt-3 border-t border-slate-800 space-y-2">
                                <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tasks</h4>
                                ${pTasks.length === 0 ? '<p class="text-slate-600 text-xs">No tasks in this project.</p>' : ''}
                                ${pTasks.map(t => `
                                    <div class="flex items-center justify-between bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                                        <div>
                                            <p class="text-sm font-medium ${t.is_completed ? 'line-through text-slate-500' : 'text-slate-200'}">${t.title}</p>
                                            <p class="text-xs text-slate-500">${t.description || ''}</p>
                                        </div>
                                        <button onclick="deleteTask(${t.id})" class="text-xs text-rose-400 hover:text-rose-300 bg-rose-950 px-2 py-1 rounded border border-rose-900">Delete</button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('');
            }

            async function createProject(e) {
                e.preventDefault();
                await fetch('/projects/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: document.getElementById('pTitle').value,
                        description: document.getElementById('pDesc').value
                    })
                });
                document.getElementById('projectForm').reset();
                loadData();
            }

            async function createTask(e) {
                e.preventDefault();
                await fetch('/tasks/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: document.getElementById('tTitle').value,
                        description: document.getElementById('tDesc').value,
                        project_id: parseInt(document.getElementById('tProjectId').value),
                        is_completed: false
                    })
                });
                document.getElementById('taskForm').reset();
                loadData();
            }

            async function deleteTask(id) {
                await fetch(`/tasks/${id}`, { method: 'DELETE' });
                loadData();
            }

            loadData();
        </script>
    </body>
    </html>
    """


# ==========================================
# MODERN SCALAR DOCS
# ==========================================

@app.get("/docs-modern", include_in_schema=False)
async def scalar_html():
    return HTMLResponse("""
    <!doctype html>
    <html>
      <head>
        <title>Task API Docs</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <script id="api-reference" data-url="/openapi.json" data-configuration='{"theme": "purple"}'></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """)


# ==========================================
# API ENDPOINTS
# ==========================================

@app.post("/projects/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, session: Session = Depends(get_session)):
    db_project = Project.from_orm(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    return session.exec(select(Project)).all()

@app.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/tasks/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    project = session.get(Project, task.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project ID does not exist")
    
    db_task = Task.from_orm(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskRead])
def list_tasks(session: Session = Depends(get_session)):
    return session.exec(select(Task)).all()

@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_update: TaskUpdate, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = task_update.dict(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
        
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return None