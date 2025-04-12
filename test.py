# print("hello,world")

# def bubble_sort(arr):
#     n = len(arr)
#     # 遍历所有数组元素
#     for i in range(n):
#         # 最后 i 个元素已经是有序的
#         for j in range(0, n-i-1):
#             # 如果当前元素大于下一个元素，则交换它们
#             if arr[j] > arr[j+1]:
#                 arr[j], arr[j+1] = arr[j+1], arr[j]
#     return arr
# test 1 
# test 2 commit  
# test 3 commit 
    
class Student:
    def __init__(self, student_id, name, birthday, class_name):
        self.student_id = student_id  # 学号
        self.name = name  # 姓名
        self.birthday = birthday  # 生日
        self.class_name = class_name  # 班级
        
    
    
    def change_class(self, new_class):
        """修改学生班级"""
        self.class_name = new_class
        print(f"{self.name}的班级已更改为: {new_class}")
    
    def display_info(self):
        """显示学生信息"""
        print(f"学号: {self.student_id}")
        print(f"姓名: {self.name}")
        print(f"生日: {self.birthday}")
        print(f"班级: {self.class_name}")

# 测试示例
if __name__ == "__main__":
    # 创建学生对象
    student1 = Student("2023001", "张三", "2005-03-15", "高三(1)班")
 #   student2 = Student("2023002", "李四", "2005-06-20", "高三(1)班")
        
    # 显示学生信息
    print("学生信息：")
    student1.display_info()
    
    
    # 修改班级
    student1.change_class("高三(2)班")
    
    # 再次显示学生信息
    print("\n修改后的学生信息：")
    student1.display_info()
    
    # # 显示学生2的信息
    # print("学生2信息：")
    # student2.display_info()

    # # 修改学生2的班级
    # student2.change_class("高三(3)班")

    # # 显示修改后的信息
    # print("\n修改后的学生2信息：")
    # student2.display_info()
