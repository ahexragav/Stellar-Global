from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.productmodels import *
from  dto import productschemas as schemas
from sqlalchemy.orm import Session
from config.database import get_db
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from typing import List
from sqlalchemy.sql import func
router = APIRouter(tags=["shop product"])

@router.get("/products/", response_model=List[schemas.CategorySummary])
def get_categories_with_representative_images(db: Session = Depends(get_db)):
    """
    Returns a list of categories with descriptions and a representative product image.
    """
    results = (
        db.query(
            ProductCategory.category_id,
            ProductCategory.category_name,
            ProductCategory.description,
            func.min(Product.product_image).label("product_image")
        )
        .join(ProductType, ProductCategory.category_id == ProductType.category_id)
        .join(Product, ProductType.type_id == Product.type_id)
        .group_by(ProductCategory.category_id, ProductCategory.category_name, ProductCategory.description)
        .all()
    )
    print(results)
    return [
        {
            "category_id": r.category_id,
            "category_name": r.category_name,
            "description": r.description,
            "product_image": r.product_image
        }
        for r in results
    ]

@router.get("/products/{category_id}", response_model=List[schemas.ProductDetail])
def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Returns all unique products within a specific category, grouped by type_id.
    """
    subquery = (
        db.query(
            Product.type_id,
            func.min(Product.product_id).label("product_id")  # Fetch the first product in each type
        )
        .join(ProductType, Product.type_id == ProductType.type_id)
        .filter(ProductType.category_id == category_id)
        .group_by(Product.type_id)
        .subquery()
    )

    products = (
        db.query(Product)
        .join(subquery, Product.product_id == subquery.c.product_id)
        .all()
    )

    if not products:
        raise HTTPException(status_code=404, detail="No products found for this category")

    return products
