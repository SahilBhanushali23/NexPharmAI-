from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.product import Product
from app.schemas.production import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "QUALITY_MANAGER"])

@router.get("", response_model=List[ProductResponse], summary="List all pharmaceutical products")
def list_products(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    query = db.query(Product)
    if status:
        query = query.filter(Product.status == status.upper())
    if search:
        fmt = f"%{search}%"
        query = query.filter((Product.product_code.ilike(fmt)) | (Product.product_name.ilike(fmt)))
    return query.order_by(Product.product_code).offset(skip).limit(limit).all()

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Create a new pharmaceutical product")
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    existing = db.query(Product).filter(Product.product_code == product_in.product_code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product code already exists")
    product = Product(
        product_code=product_in.product_code.upper(),
        product_name=product_in.product_name,
        description=product_in.description,
        batch_size=product_in.batch_size,
        standard_production_time=product_in.standard_production_time,
        required_materials=product_in.required_materials,
        status=product_in.status.upper()
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/{product_id}", response_model=ProductResponse, summary="Get product details")
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    product = db.query(Product).filter(
        (Product.id == product_id) | (Product.product_code == product_id)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/{product_id}", response_model=ProductResponse, summary="Update product specifications")
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    product = db.query(Product).filter(
        (Product.id == product_id) | (Product.product_code == product_id)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product_in.product_name: product.product_name = product_in.product_name
    if product_in.description is not None: product.description = product_in.description
    if product_in.batch_size is not None: product.batch_size = product_in.batch_size
    if product_in.standard_production_time is not None: product.standard_production_time = product_in.standard_production_time
    if product_in.required_materials is not None: product.required_materials = product_in.required_materials
    if product_in.status: product.status = product_in.status.upper()
    db.commit()
    db.refresh(product)
    return product
