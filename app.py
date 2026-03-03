from flask import Flask, render_template, request, redirect
from datetime import datetime
from models import get_db_connection, create_tables

app = Flask(__name__)

# Create tables when app starts
create_tables()

