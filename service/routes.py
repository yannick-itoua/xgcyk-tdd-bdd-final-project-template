from flask import jsonify, request, abort, url_for
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app

######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Vérifie si le service fonctionne correctement"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK

######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Page d'accueil du service"""
    return app.send_static_file("index.html")

######################################################################
# U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Vérifie si le type de contenu est correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("Content-Type non spécifié.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type doit être {content_type}",
        )

    if request.headers["Content-Type"] != content_type:
        app.logger.error("Content-Type invalide : %s", request.headers["Content-Type"])
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type doit être {content_type}",
        )

######################################################################
# CREATE A NEW PRODUCT
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """Créer un nouveau produit"""
    app.logger.info("Requête pour créer un produit...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Données reçues : %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Produit avec l'ID [%s] enregistré !", product.id)

    location_url = url_for("get_products", product_id=product.id, _external=True)
    return jsonify(product.serialize()), status.HTTP_201_CREATED, {"Location": location_url}

######################################################################
# LIST ALL PRODUCTS
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    """Retourne une liste de produits avec filtres optionnels"""
    app.logger.info("Requête pour lister les produits...")

    name = request.args.get("name")
    category = request.args.get("category")
    available = request.args.get("available")

    try:
        products = Product.all()
        if name:
            app.logger.info("Filtrage par nom : %s", name)
            products = Product.find_by_name(name)
        if category:
            app.logger.info("Filtrage par catégorie : %s", category)
            category_value = getattr(Category, category.upper(), None)
            if not category_value:
                abort(status.HTTP_400_BAD_REQUEST, f"Catégorie invalide : {category}")
            products = [product for product in products if product.category == category_value]
        if available:
            app.logger.info("Filtrage par disponibilité : %s", available)
            available_value = available.lower() in ["true", "yes", "1"]
            products = [product for product in products if product.available == available_value]

        results = [product.serialize() for product in products]
        app.logger.info("[%s] Produits retournés", len(results))
        return jsonify(results), status.HTTP_200_OK

    except Exception as e:
        app.logger.error("Erreur lors de la liste des produits : %s", e)
        abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "Erreur interne du serveur")

######################################################################
# READ A PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """Récupère un produit spécifique"""
    app.logger.info("Requête pour récupérer un produit avec l'ID [%s]", product_id)

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Produit avec l'ID '{product_id}' introuvable.")

    app.logger.info("Produit trouvé : %s", product.name)
    return jsonify(product.serialize()), status.HTTP_200_OK

######################################################################
# UPDATE AN EXISTING PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """Met à jour un produit existant"""
    app.logger.info("Requête pour mettre à jour un produit avec l'ID [%s]", product_id)
    check_content_type("application/json")

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Produit avec l'ID '{product_id}' introuvable.")

    try:
        product.deserialize(request.get_json())
        product.id = product_id
        product.update()
    except KeyError as e:
        abort(status.HTTP_400_BAD_REQUEST, f"Données manquantes : {str(e)}")
    except ValueError as e:
        abort(status.HTTP_400_BAD_REQUEST, f"Données invalides : {str(e)}")

    return jsonify(product.serialize()), status.HTTP_200_OK

######################################################################
# DELETE A PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """Supprime un produit"""
    app.logger.info("Requête pour supprimer un produit avec l'ID [%s]", product_id)

    product = Product.find(product_id)
    if product:
        product.delete()

    return "", status.HTTP_204_NO_CONTENT
