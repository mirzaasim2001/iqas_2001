from flask import Flask, render_template, request, redirect, session
import json
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ---------------- HOME ----------------
@app.route("/")
def home():
    with open("data/niches.json") as f:
        niches = json.load(f)

    with open("data/featured_products.json") as f:
        featured = json.load(f)

    return render_template(
        "home.html",
        niches=niches,
        featured=featured
    )



@app.route("/admin/delete-niche/<niche>")
def delete_niche(niche):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    # remove from niches.json
    with open("data/niches.json", "r+") as f:
        niches = json.load(f)
        if niche in niches:
            niches.remove(niche)
        f.seek(0)
        json.dump(niches, f, indent=2)
        f.truncate()

    # remove products under this niche
    with open("data/products.json", "r+") as f:
        products = json.load(f)
        products.pop(niche, None)
        f.seek(0)
        json.dump(products, f, indent=2)
        f.truncate()

    return redirect("/admin/panel")


@app.route("/admin/edit-niche", methods=["POST"])
def edit_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    old = request.form["old_niche"]
    new = request.form["new_niche"].lower()

    # update niches.json
    with open("data/niches.json", "r+") as f:
        niches = json.load(f)
        if old in niches:
            niches.remove(old)
            niches.append(new)
        f.seek(0)
        json.dump(niches, f, indent=2)
        f.truncate()

    # move products to new niche key
    with open("data/products.json", "r+") as f:
        products = json.load(f)
        products[new] = products.pop(old, [])
        f.seek(0)
        json.dump(products, f, indent=2)
        f.truncate()

    return redirect("/admin/panel")


# ---------------- NICHE PAGE ----------------
@app.route("/niche/<name>")
def niche(name):
    with open("data/products.json") as f:
        products_by_niche = json.load(f)

    products = products_by_niche.get(name, [])
    return render_template("niche.html", niche=name, products=products)


# ---------------- SAVED (PLACEHOLDER) ----------------
@app.route("/saved")
def saved():
    return render_template("saved.html")


# ---------------- CONTACT ----------------
@app.route("/contact")
def contact():
    return render_template("contact.html")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USERNAME and
            request.form["password"] == ADMIN_PASSWORD
        ):
            session["admin"] = ADMIN_USERNAME
            return redirect("/admin/panel")

    return render_template("admin_login.html")


# ---------------- ADMIN PANEL ----------------
@app.route("/admin/panel")
def admin_panel():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    with open("data/products.json") as f:
        products = json.load(f)

    return render_template("admin_panel.html", products=products)


# ---------------- ADD NICHE ----------------
@app.route("/admin/add-niche", methods=["POST"])
def add_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    niche = request.form["niche"].lower()

    with open("data/niches.json", "r+") as f:
        niches = json.load(f)
        if niche not in niches:
            niches.append(niche)
        f.seek(0)
        json.dump(niches, f, indent=2)
        f.truncate()

    # ensure niche exists in products.json.json
    with open("data/products.json.json", "r+") as f:
        products = json.load(f)
        products.setdefault(niche, [])
        f.seek(0)
        json.dump(products, f, indent=2)
        f.truncate()

    return redirect("/admin/panel")


# ---------------- ADD PRODUCT ----------------
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    niche = request.form["niche"]

    product = {
        "title": request.form["title"],
        "price": request.form["price"],
        "image": request.form["image"],
        "link": request.form["link"]
    }

    with open("data/products.json", "r+") as f:
        data = json.load(f)
        data.setdefault(niche, [])
        data[niche].insert(0, product)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    return redirect("/admin/panel")


# ---------------- FEATURE PRODUCT ON HOME ----------------
@app.route("/admin/feature", methods=["POST"])
def feature_product():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    product = {
        "title": request.form["title"],
        "price": request.form["price"],
        "image": request.form["image"],
        "link": request.form["link"]
    }

    with open("data/featured_products.json", "r+") as f:
        featured = json.load(f)
        featured.insert(0, product)
        f.seek(0)
        json.dump(featured[:6], f, indent=2)
        f.truncate()

    return redirect("/")


@app.route("/admin/delete-product/<niche>/<int:index>")
def delete_product(niche, index):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    with open("data/products.json", "r+") as f:
        data = json.load(f)
        if niche in data and index < len(data[niche]):
            data[niche].pop(index)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    return redirect("/admin/panel")


@app.route("/admin/edit-product/<niche>/<int:index>", methods=["GET", "POST"])
def edit_product(niche, index):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    with open("data/products.json") as f:
        data = json.load(f)

    product = data[niche][index]

    if request.method == "POST":
        product["title"] = request.form["title"]
        product["price"] = request.form["price"]
        product["image"] = request.form["image"]
        product["link"] = request.form["link"]

        with open("data/products.json", "w") as f:
            json.dump(data, f, indent=2)

        return redirect("/admin/panel")

    return render_template(
        "edit_product.html",
        product=product,
        niche=niche,
        index=index
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
