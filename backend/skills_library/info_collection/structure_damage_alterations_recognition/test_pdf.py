"""
快速测试脚本 - 检查PDF是否能被处理（使用 PyMuPDF，无需 Poppler）
请从 backend 目录运行: python -m skills_library.info_collection.structure_damage_alterations_recognition.test_pdf
"""
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parents[4]
if _backend not in sys.path:
    sys.path.insert(0, str(_backend))

from services.tools.pdf_to_image import pdf_to_images


def test_pdf(pdf_path):
    """测试PDF文件"""
    print(f"📄 测试PDF: {pdf_path}")
    print("=" * 60)

    if not Path(pdf_path).exists():
        print("❌ 文件不存在!")
        return False

    print(f"✅ 文件存在: {Path(pdf_path).stat().st_size / 1024:.2f} KB")

    try:
        print("\n🔄 正在转换PDF为图片 (PyMuPDF)...")
        images = pdf_to_images(pdf_path, dpi=200, first_page=1, last_page=1)

        if images:
            img = images[0]
            print("✅ PDF转换成功!")
            print(f"   - 页数: 至少1页")
            print(f"   - 第一页尺寸: {img.size[0]} x {img.size[1]} 像素")
            print(f"   - 模式: {img.mode}")

            test_output = Path("data/test_output.jpg")
            test_output.parent.mkdir(parents=True, exist_ok=True)
            img.save(test_output)
            print(f"   - 测试图片已保存: {test_output}")
            return True
        else:
            print("❌ PDF转换失败: 没有生成图片")
            return False
    except Exception as e:
        print(f"❌ 处理失败: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    pdf_path = r"D:\All_about_AI\报告模板及AI资料\模板_2025-2-10\完整报告及资料\建材新村_危房鉴定\建材新村_部分2.pdf"

    success = test_pdf(pdf_path)

    if success:
        print("\n" + "=" * 60)
        print("✨ PDF文件可以正常处理 (PyMuPDF)!")
        print("\n📝 下一步:")
        print("   1. 在 .env 文件中配置 DASHSCOPE_API_KEY")
        print("   2. 运行: python parse.py \"" + pdf_path + "\" -o data/output -f json")
    else:
        print("\n" + "=" * 60)
        print("❌ PDF处理失败，请检查:")
        print("   1. 是否已安装 pymupdf: pip install pymupdf")
        print("   2. PDF文件是否损坏")
