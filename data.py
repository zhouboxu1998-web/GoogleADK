import os
from dotenv import load_dotenv

load_dotenv()
# 1. 创建存放评价内容的文件夹
base_dir = os.getenv('NEO4J_IMPORT_DIR')
reviews_dir = os.path.join(base_dir, 'product_review')

os.makedirs(base_dir, exist_ok=True)
os.makedirs(reviews_dir, exist_ok=True)

# 2. 生成产品的基本信息
products_data = """product_id,product_name,category,retail_price
PRD-01,Linkoping Bed,Bedroom,299.00
PRD-02,Jonkoping Coffee Table,Living Room,89.00
PRD-03,Uppsala Sofa,Living Room,499.00
PRD-04,Stockholm Chair,Dining,69.00
PRD-05,Vasteras Bookshelf,Office,129.00
PRD-06,Malmo Desk,Office,149.00
PRD-07,Helsingborg Dresser,Bedroom,199.00
PRD-08,Orebro Lamp,Lighting,39.00
PRD-09,Gothenburg Table,Dining,249.00
PRD-10,Norrkoping Nightstand,Bedroom,49.00"""
with open(os.path.join(base_dir, 'products.csv'), 'w', encoding='utf-8') as f: f.write(products_data)

# 3. 生成装配件/组件
assemblies_data = """assembly_id,product_id,assembly_name
ASM-001,PRD-01,Bed Frame Assembly
ASM-002,PRD-01,Slatted Bed Base
ASM-003,PRD-03,Sofa Frame Assembly
ASM-004,PRD-03,Cushion Set
ASM-005,PRD-06,Desk Drawer Unit"""
with open(os.path.join(base_dir, 'assemblies.csv'), 'w', encoding='utf-8') as f: f.write(assemblies_data)

# 4. 生成底层零件清单
parts_data = """part_id,part_name,material
PRT-101,Side Rail,Pine Wood
PRT-102,Center Support Beam,Steel
PRT-103,M8 Screw,Stainless Steel
PRT-104,Sofa Leg,Oak Wood
PRT-105,Foam Insert,Polyurethane
PRT-106,Fabric Cover,Cotton Blend
PRT-107,Drawer Handle,Aluminum"""
with open(os.path.join(base_dir, 'parts.csv'), 'w', encoding='utf-8') as f: f.write(parts_data)

# 5. 生成组件构成表
components_data = """component_id,parent_assembly_id,part_id,quantity
C-01,ASM-001,PRT-101,2
C-02,ASM-001,PRT-103,12
C-03,ASM-002,PRT-102,1
C-04,ASM-003,PRT-104,4
C-05,ASM-004,PRT-105,3
C-06,ASM-004,PRT-106,3"""
with open(os.path.join(base_dir, 'components.csv'), 'w', encoding='utf-8') as f: f.write(components_data)

# 6. 生成供应商信息
suppliers_data = """supplier_id,supplier_name,country,contact_email
SUP-01,Nordic Timber Co.,Sweden,contact@nordictimber.se
SUP-02,EuroSteel Manufacturing,Germany,sales@eurosteel.de
SUP-03,Textile Weavers Ltd.,India,export@textileweavers.in
SUP-04,Smaland Fasteners,Sweden,info@smalandfasteners.se"""
with open(os.path.join(base_dir, 'suppliers.csv'), 'w', encoding='utf-8') as f: f.write(suppliers_data)

# 7. 生成零件与供应商的映射表
mapping_data = """part_id,supplier_id,lead_time_days,unit_cost
PRT-101,SUP-01,14,25.00
PRT-102,SUP-02,21,15.50
PRT-103,SUP-04,7,0.10
PRT-104,SUP-01,14,8.00
PRT-105,SUP-03,30,12.00
PRT-106,SUP-03,30,18.00
PRT-107,SUP-02,21,2.50"""
with open(os.path.join(base_dir, 'part_supplier_mapping.csv'), 'w', encoding='utf-8') as f: f.write(mapping_data)

# 8. 批量生成 10 个 Markdown 评价文件到 product_reviews 文件夹中
reviews_list = [
    ('linkoping_bed', 'Linkoping Bed'),
    ('jonkoping_coffee_table', 'Jonkoping Coffee Table'),
    ('uppsala_sofa', 'Uppsala Sofa'),
    ('stockholm_chair', 'Stockholm Chair'),
    ('vasteras_bookshelf', 'Vasteras Bookshelf'),
    ('malmo_desk', 'Malmo Desk'),
    ('helsingborg_dresser', 'Helsingborg Dresser'),
    ('orebro_lamp', 'Orebro Lamp'),
    ('gothenburg_table', 'Gothenburg Table'),
    ('norrkoping_nightstand', 'Norrkoping Nightstand')
]

for filename, product_name in reviews_list:
    md_content = f"""# Customer Reviews for {product_name}

## Review 1
**Rating:** 5/5
**Comment:** The {product_name} is fantastic! Assembly was relatively straightforward, and the quality of the materials is excellent. 

## Review 2
**Rating:** 4/5
**Comment:** Good value for the price. The packaging was a bit damaged upon arrival, but the product itself was unharmed. 

## Review 3
**Rating:** 3/5
**Comment:** It's okay. The BOM (Bill of Materials) instructions were quite complex, and it took me a few hours to put together using all the individual components.
"""
    file_path = os.path.join(reviews_dir, f'{filename}_reviews.md')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

print(f"✅ 成功！所有文件已成功生成到目标目录：\n{base_dir}")