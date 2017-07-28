import json

from flask import request, Response, url_for, redirect, render_template
from jsonschema import validate, ValidationError

from . import models
from models import Post
from . import decorators
from posts import app
from .database import session


post_schema = {
    "properties": {
        "title" : {"type" : "string"},
        "body": {"type": "string"}
    },
    "required": ["title", "body"]
}

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
    """ Get a list of posts """
    # Get the querystring arguments
    title_like = request.args.get("title_like")
    body_like = request.args.get("body_like")

    # Get and filter the posts from the database
    posts = session.query(models.Post)
    if title_like:
        posts = posts.filter(models.Post.title.contains(title_like))
    posts = posts.order_by(models.Post.id)
    
    if title_like and body_like:
        posts = posts.filter(models.Post.title.contains(title_like))
        posts = posts.filter(models.Post.title.contains(body_like))
    posts = posts.order_by(models.Post.id)

    # Convert the posts to JSON and return a response
    data = json.dumps([post.as_dictionary() for post in posts])
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/posts/<int:id>", methods=["GET"])
def post_get(id):
    """ Single post endpoint """
    # Get the post from the database
    post = session.query(models.Post).get(id)

    # Check whether the post exists
    # If not return a 404 with a helpful message
    if not post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Return the post as JSON
    data = json.dumps(post.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts/<id>/delete", methods=["GET"])
def post_delete(id):
    """ Single post endpoint """
    # Get the post from the database
    post = session.query(models.Post).get(id)
    
    # Check whether the post exists
    # If not return a 404 with a helpful message
    if not post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Delete post from the database
    session.delete(post)
    session.commit()
    
    return redirect(url_for("posts_get"), 302)
    

@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_post():
    """ Add a new post """
    data = request.json
    
    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    # Add the post to the database
    post = models.Post(title=data["title"], body=data["body"])
    session.add(post)
    session.commit()
    
    # Return a 201 Created, containing the post as JSON and with the 
    # Location header set to the location of the post
    data = json.dumps(post.as_dictionary())
    headers = {"Location": url_for("post_get", id=post.id)}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")

@app.route("/api/post/<id>/edit", methods=["GET", "PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def edits_post(id):
    """ Edit a post """
    
    if request.method == "GET":
        post = session.query(models.Post).get(id)
        return render_template("edit_entry.html", post=post)
    
    elif request.method == "PUT":
        # Query the post by its id and then update it with the edits
        post=session.query(Post).filter(Post.id==id).one()
        post.title = request.form["title"]
        post.body = request.form["body"]
        session.add(post)
        session.commit()
        return redirect(url_for("posts_get", 302))