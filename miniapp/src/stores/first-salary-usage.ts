/**
 * 第一笔工资用途 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  listFirstSalaryUsage,
  createFirstSalaryUsage,
  updateFirstSalaryUsage,
  deleteFirstSalaryUsage,
  getCategoryStatistics,
  type FirstSalaryUsageRecord,
  type FirstSalaryUsageCreate,
  type FirstSalaryUsageUpdate,
  type FirstSalaryUsageListParams,
  type UsageCategory,
} from '@/api/first-salary-usage'

export const useFirstSalaryUsageStore = defineStore('firstSalaryUsage', () => {
  // State
  const records = ref<FirstSalaryUsageRecord[]>([])
  const total = ref(0)
  const loading = ref(false)
  const statistics = ref<Record<UsageCategory, number>>({} as Record<UsageCategory, number>)
  const statisticsLoading = ref(false)

  // Getters
  const recordsByCategory = computed(() => {
    const grouped: Record<UsageCategory, FirstSalaryUsageRecord[]> = {} as any
    records.value.forEach(record => {
      if (!grouped[record.usage_category]) {
        grouped[record.usage_category] = []
      }
      grouped[record.usage_category].push(record)
    })
    return grouped
  })

  const totalAmount = computed(() => {
    return records.value.reduce((sum, record) => sum + record.amount, 0)
  })

  const categoryAmounts = computed(() => {
    const amounts: Record<UsageCategory, number> = {} as any
    records.value.forEach(record => {
      amounts[record.usage_category] = (amounts[record.usage_category] || 0) + record.amount
    })
    return amounts
  })

  // Actions
  const fetchRecords = async (params?: FirstSalaryUsageListParams) => {
    loading.value = true
    try {
      const response = await listFirstSalaryUsage(params)
      records.value = response.items
      total.value = response.total
      return response
    } catch (error) {
      console.error('获取第一笔工资用途记录失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createRecord = async (data: FirstSalaryUsageCreate) => {
    loading.value = true
    try {
      const newRecord = await createFirstSalaryUsage(data)
      records.value.unshift(newRecord)
      total.value += 1
      return newRecord
    } catch (error) {
      console.error('创建第一笔工资用途记录失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateRecord = async (recordId: string, data: FirstSalaryUsageUpdate) => {
    loading.value = true
    try {
      const updatedRecord = await updateFirstSalaryUsage(recordId, data)
      const index = records.value.findIndex(r => r.id === recordId)
      if (index !== -1) {
        records.value[index] = updatedRecord
      }
      return updatedRecord
    } catch (error) {
      console.error('更新第一笔工资用途记录失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteRecord = async (recordId: string) => {
    loading.value = true
    try {
      await deleteFirstSalaryUsage(recordId)
      const index = records.value.findIndex(r => r.id === recordId)
      if (index !== -1) {
        records.value.splice(index, 1)
        total.value -= 1
      }
    } catch (error) {
      console.error('删除第一笔工资用途记录失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchStatistics = async (params?: { salary_record_id?: string }) => {
    statisticsLoading.value = true
    try {
      const response = await getCategoryStatistics(params)
      statistics.value = response.statistics
      return response
    } catch (error) {
      console.error('获取分类统计失败:', error)
      throw error
    } finally {
      statisticsLoading.value = false
    }
  }

  const clearRecords = () => {
    records.value = []
    total.value = 0
    statistics.value = {} as any
  }

  return {
    // State
    records,
    total,
    loading,
    statistics,
    statisticsLoading,
    // Getters
    recordsByCategory,
    totalAmount,
    categoryAmounts,
    // Actions
    fetchRecords,
    createRecord,
    updateRecord,
    deleteRecord,
    fetchStatistics,
    clearRecords,
  }
})
