class Solution(object):
    def removeDuplicates(self, nums):
        if not nums:
            return 0
            
        k = 1  # Первый элемент всегда уникален
        for i in range(1, len(nums)):
            if nums[i] != nums[k-1]:  # Сравниваем с последним уникальным
                nums[k] = nums[i]     # Записываем на позицию k
                k += 1
        return k

nums = [1,1,2]
solution = Solution()
result = solution.removeDuplicates(nums)
print(result)
