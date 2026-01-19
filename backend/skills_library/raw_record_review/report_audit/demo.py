import json
from audit_engine import run_audit

# 模拟一个有问题的报告文本
report_text = """
一、项目概况
项目名称：阳关小区 10# 楼
建筑面积：5600.5 m2
建成年代：2005年
结构层数：地上6层，地下1层。

二、检测结论
工程名称：阳光小区10号楼 （*注：这里写成了“阳光”，且“10号”与“10#”不一致*）
该房屋建筑面积 5600.50 平方米。（*注：这里多了个0*）
建成于2004年。（*注：年代也不一致*）

三、构件强度检测
1. 砌筑砂浆
检测结果显示，M1测区砂浆抗压强度换算值为 5.0 MPa，M2测区为 4.85 MPa。（*注：4.85 保留了2位，错误*）
推定值为 5 MPa。（*注：未保留小数，错误*）

2. 混凝土及其它
碳化深度平均值实测如下：
C1测区碳化深度平均值：1.0 mm （OK）
C2测区碳化深度平均值：1.2 mm （*注：不是0.5倍数，错误*）
C3测区碳化深度平均值：2 mm   （*注：无小数，错误*）
"""

print("Running Audit on Check...")
result = run_audit(report_text)

print("\n--- Audit Report (JSON) ---")
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n--- Summary ---")
print(f"Overall Status: {result['overall_status']}")
print(result['summary'])
