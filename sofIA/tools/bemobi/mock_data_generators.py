"""
Mock Data Generators for BEMOBI Integration

This module provides realistic mock data generators for different regions
to simulate BEMOBI payment gateway responses during hackathon demonstrations.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class Region(Enum):
    """Supported regions"""
    LATAM = "latam"
    AFRICA = "africa"
    ASIA = "asia"


@dataclass
class MockMerchant:
    """Mock merchant data"""
    merchant_id: str
    store_name: str
    region: Region
    currency: str
    category: str
    description: str
    supported_payment_methods: List[str]
    average_transaction_value: float
    monthly_volume: float


@dataclass
class MockProduct:
    """Mock product data"""
    product_id: str
    name: str
    description: str
    price: float
    currency: str
    category: str
    merchant_id: str


class MockDataGenerator:
    """Generates realistic mock data for BEMOBI integration"""
    
    def __init__(self, region: Region = Region.LATAM):
        self.region = region
        self.merchants = self._generate_merchants()
        self.products = self._generate_products()
    
    def _generate_merchants(self) -> List[MockMerchant]:
        """Generate mock merchants for the region"""
        if self.region == Region.LATAM:
            return [
                MockMerchant(
                    merchant_id="bemobi_latam_001",
                    store_name="Café do João",
                    region=Region.LATAM,
                    currency="BRL",
                    category="food_beverage",
                    description="Traditional Brazilian coffee shop",
                    supported_payment_methods=["pix", "card", "boleto"],
                    average_transaction_value=15.50,
                    monthly_volume=25000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_latam_002",
                    store_name="Mercado Central",
                    region=Region.LATAM,
                    currency="BRL",
                    category="grocery",
                    description="Local grocery store with fresh produce",
                    supported_payment_methods=["pix", "card", "boleto"],
                    average_transaction_value=85.00,
                    monthly_volume=150000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_latam_003",
                    store_name="Tech Store São Paulo",
                    region=Region.LATAM,
                    currency="BRL",
                    category="electronics",
                    description="Electronics and gadgets store",
                    supported_payment_methods=["card", "pix"],
                    average_transaction_value=450.00,
                    monthly_volume=500000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_latam_004",
                    store_name="Farmácia Popular",
                    region=Region.LATAM,
                    currency="BRL",
                    category="pharmacy",
                    description="Community pharmacy with health products",
                    supported_payment_methods=["pix", "card", "boleto"],
                    average_transaction_value=35.00,
                    monthly_volume=75000.00
                )
            ]
        
        elif self.region == Region.AFRICA:
            return [
                MockMerchant(
                    merchant_id="bemobi_africa_001",
                    store_name="Tech Store Lagos",
                    region=Region.AFRICA,
                    currency="NGN",
                    category="electronics",
                    description="Mobile phones and electronics in Lagos",
                    supported_payment_methods=["card", "bank_transfer", "mobile_money"],
                    average_transaction_value=45000.00,
                    monthly_volume=2500000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_africa_002",
                    store_name="Market Square Accra",
                    region=Region.AFRICA,
                    currency="GHS",
                    category="grocery",
                    description="Traditional market with local products",
                    supported_payment_methods=["mobile_money", "bank_transfer"],
                    average_transaction_value=85.00,
                    monthly_volume=150000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_africa_003",
                    store_name="Nairobi Electronics",
                    region=Region.AFRICA,
                    currency="KES",
                    category="electronics",
                    description="Electronics store in Nairobi",
                    supported_payment_methods=["card", "mobile_money"],
                    average_transaction_value=12000.00,
                    monthly_volume=800000.00
                )
            ]
        
        else:  # ASIA
            return [
                MockMerchant(
                    merchant_id="bemobi_asia_001",
                    store_name="Bangkok Electronics",
                    region=Region.ASIA,
                    currency="THB",
                    category="electronics",
                    description="Electronics and gadgets in Bangkok",
                    supported_payment_methods=["card", "bank_transfer", "wallet"],
                    average_transaction_value=2500.00,
                    monthly_volume=500000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_asia_002",
                    store_name="Jakarta Food Court",
                    region=Region.ASIA,
                    currency="IDR",
                    category="food_beverage",
                    description="Traditional Indonesian food court",
                    supported_payment_methods=["wallet", "bank_transfer"],
                    average_transaction_value=45000.00,
                    monthly_volume=200000.00
                ),
                MockMerchant(
                    merchant_id="bemobi_asia_003",
                    store_name="Manila Shopping Center",
                    region=Region.ASIA,
                    currency="PHP",
                    category="retail",
                    description="Shopping center with various stores",
                    supported_payment_methods=["card", "wallet", "bank_transfer"],
                    average_transaction_value=850.00,
                    monthly_volume=300000.00
                )
            ]
    
    def _generate_products(self) -> List[MockProduct]:
        """Generate mock products for merchants"""
        products = []
        
        for merchant in self.merchants:
            if merchant.category == "food_beverage":
                products.extend([
                    MockProduct(
                        product_id=f"{merchant.merchant_id}_prod_001",
                        name="Coffee",
                        description="Fresh brewed coffee",
                        price=5.50 if merchant.currency == "BRL" else 45000.00,
                        currency=merchant.currency,
                        category="beverage",
                        merchant_id=merchant.merchant_id
                    ),
                    MockProduct(
                        product_id=f"{merchant.merchant_id}_prod_002",
                        name="Lunch Special",
                        description="Daily lunch special",
                        price=12.00 if merchant.currency == "BRL" else 85000.00,
                        currency=merchant.currency,
                        category="food",
                        merchant_id=merchant.merchant_id
                    )
                ])
            
            elif merchant.category == "electronics":
                products.extend([
                    MockProduct(
                        product_id=f"{merchant.merchant_id}_prod_001",
                        name="Smartphone",
                        description="Latest smartphone model",
                        price=450.00 if merchant.currency == "BRL" else 45000.00,
                        currency=merchant.currency,
                        category="mobile",
                        merchant_id=merchant.merchant_id
                    ),
                    MockProduct(
                        product_id=f"{merchant.merchant_id}_prod_002",
                        name="Laptop",
                        description="High-performance laptop",
                        price=1200.00 if merchant.currency == "BRL" else 120000.00,
                        currency=merchant.currency,
                        category="computing",
                        merchant_id=merchant.merchant_id
                    )
                ])
            
            elif merchant.category == "grocery":
                products.extend([
                    MockProduct(
                        product_id=f"{merchant.merchant_id}_prod_001",
                        name="Grocery Basket",
                        description="Weekly grocery essentials",
                        price=85.00 if merchant.currency == "BRL" else 85000.00,
                        currency=merchant.currency,
                        category="groceries",
                        merchant_id=merchant.merchant_id
                    )
                ])
        
        return products
    
    def get_random_merchant(self) -> MockMerchant:
        """Get a random merchant from the region"""
        return random.choice(self.merchants)
    
    def get_merchant_by_id(self, merchant_id: str) -> Optional[MockMerchant]:
        """Get merchant by ID"""
        for merchant in self.merchants:
            if merchant.merchant_id == merchant_id:
                return merchant
        return None
    
    def get_products_by_merchant(self, merchant_id: str) -> List[MockProduct]:
        """Get products for a specific merchant"""
        return [product for product in self.products if product.merchant_id == merchant_id]
    
    def get_random_product(self, merchant_id: Optional[str] = None) -> MockProduct:
        """Get a random product, optionally filtered by merchant"""
        if merchant_id:
            merchant_products = self.get_products_by_merchant(merchant_id)
            return random.choice(merchant_products) if merchant_products else self.products[0]
        return random.choice(self.products)
    
    def generate_payment_intent_data(self, merchant_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Generate realistic payment intent data"""
        merchant = self.get_merchant_by_id(merchant_id)
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")
        
        if amount is None:
            # Generate realistic amount based on merchant's average transaction
            base_amount = merchant.average_transaction_value
            amount = base_amount * random.uniform(0.5, 2.0)
        
        return {
            "merchant_id": merchant_id,
            "amount": round(amount, 2),
            "currency": merchant.currency,
            "description": f"Purchase from {merchant.store_name}",
            "category": merchant.category,
            "region": merchant.region.value,
            "supported_payment_methods": merchant.supported_payment_methods
        }
    
    def generate_payment_response_data(self, payment_intent_data: Dict[str, Any], 
                                     payment_method: str) -> Dict[str, Any]:
        """Generate realistic payment response data"""
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        
        # Simulate processing time
        processed_at = now + timedelta(seconds=random.randint(1, 5))
        
        return {
            "transaction_id": transaction_id,
            "payment_intent_id": f"pi_{uuid.uuid4().hex[:16]}",
            "amount": payment_intent_data["amount"],
            "currency": payment_intent_data["currency"],
            "payment_method": payment_method,
            "status": "succeeded",
            "created_at": now.isoformat(),
            "processed_at": processed_at.isoformat(),
            "merchant_id": payment_intent_data["merchant_id"],
            "region": payment_intent_data["region"]
        }
    
    def get_regional_payment_methods(self) -> List[str]:
        """Get payment methods common in the region"""
        if self.region == Region.LATAM:
            return ["pix", "card", "boleto", "bank_transfer"]
        elif self.region == Region.AFRICA:
            return ["mobile_money", "bank_transfer", "card"]
        else:  # ASIA
            return ["wallet", "bank_transfer", "card"]
    
    def get_regional_currencies(self) -> List[str]:
        """Get currencies used in the region"""
        if self.region == Region.LATAM:
            return ["BRL", "ARS", "CLP", "COP", "MXN"]
        elif self.region == Region.AFRICA:
            return ["NGN", "GHS", "KES", "ZAR", "EGP"]
        else:  # ASIA
            return ["THB", "IDR", "PHP", "VND", "MYR"]


# Regional data generators
LATAM_GENERATOR = MockDataGenerator(Region.LATAM)
AFRICA_GENERATOR = MockDataGenerator(Region.AFRICA)
ASIA_GENERATOR = MockDataGenerator(Region.ASIA)


def get_regional_generator(region: str) -> MockDataGenerator:
    """Get the appropriate data generator for a region"""
    region_enum = Region(region.lower())
    if region_enum == Region.LATAM:
        return LATAM_GENERATOR
    elif region_enum == Region.AFRICA:
        return AFRICA_GENERATOR
    else:
        return ASIA_GENERATOR


def generate_demo_scenario(region: str = "latam") -> Dict[str, Any]:
    """Generate a complete demo scenario for the region"""
    generator = get_regional_generator(region)
    merchant = generator.get_random_merchant()
    product = generator.get_random_product(merchant.merchant_id)
    
    payment_intent = generator.generate_payment_intent_data(
        merchant.merchant_id, 
        product.price
    )
    
    payment_method = random.choice(merchant.supported_payment_methods)
    payment_response = generator.generate_payment_response_data(
        payment_intent, 
        payment_method
    )
    
    return {
        "region": region,
        "merchant": {
            "merchant_id": merchant.merchant_id,
            "store_name": merchant.store_name,
            "category": merchant.category,
            "currency": merchant.currency
        },
        "product": {
            "product_id": product.product_id,
            "name": product.name,
            "price": product.price,
            "currency": product.currency
        },
        "payment_intent": payment_intent,
        "payment_response": payment_response,
        "demo_message": f"User wants to buy {product.name} from {merchant.store_name} for {product.currency} {product.price:.2f}"
    }
