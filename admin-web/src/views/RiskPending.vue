<template>
  <div>
    <h2 class="page-title">风控待审</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="帖子待审" name="posts">
        <div class="toolbar">
          <el-button type="primary" aria-label="刷新帖子列表" @click="fetchPosts">刷新</el-button>
        </div>
        <el-table v-loading="postsLoading" :data="posts" stripe aria-label="待审帖子列表">
          <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
          <el-table-column prop="anonymous_name" label="匿名昵称" width="120" />
          <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="90" />
          <el-table-column prop="view_count" label="浏览" width="70" />
          <el-table-column prop="like_count" label="点赞" width="70" />
          <el-table-column prop="comment_count" label="评论" width="70" />
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link aria-label="查看帖子详情" @click="openPostDetail(row)">详情</el-button>
              <el-button type="success" link aria-label="通过该帖子" @click="approvePost(row)">通过</el-button>
              <el-button type="warning" link aria-label="拒绝该帖子" @click="rejectPost(row)">拒绝</el-button>
              <el-button v-if="row.status === 'normal'" type="warning" link aria-label="隐藏该帖子" @click="hidePost(row)">隐藏</el-button>
              <el-button type="danger" link aria-label="删除该帖子" @click="deletePost(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="postsPage"
          v-model:page-size="postsPageSize"
          :total="postsTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="pagination"
          aria-label="帖子分页"
          @current-change="fetchPosts"
          @size-change="fetchPosts"
        />
      </el-tab-pane>
      <el-tab-pane label="评论待审" name="comments">
        <div class="toolbar">
          <el-button type="primary" aria-label="刷新评论列表" @click="fetchComments">刷新</el-button>
        </div>
        <el-table v-loading="commentsLoading" :data="comments" stripe aria-label="待审评论列表">
          <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
          <el-table-column prop="post_id" label="帖子ID" width="280" show-overflow-tooltip />
          <el-table-column prop="anonymous_name" label="匿名昵称" width="120" />
          <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
          <el-table-column prop="like_count" label="点赞" width="70" />
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button type="success" link aria-label="通过该评论" @click="approveComment(row)">通过</el-button>
              <el-button type="warning" link aria-label="拒绝该评论" @click="rejectComment(row)">拒绝</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="commentsPage"
          v-model:page-size="commentsPageSize"
          :total="commentsTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="pagination"
          aria-label="评论分页"
          @current-change="fetchComments"
          @size-change="fetchComments"
        />
      </el-tab-pane>
    </el-tabs>
    <el-dialog v-model="postDetailVisible" title="帖子详情" width="600px" aria-label="帖子详情对话框">
      <template v-if="currentPost">
        <p><strong>ID：</strong>{{ currentPost.id }}</p>
        <p><strong>匿名昵称：</strong>{{ currentPost.anonymous_name }}</p>
        <p><strong>类型：</strong>{{ currentPost.type }}</p>
        <p><strong>内容：</strong></p>
        <div class="content-block">{{ currentPost.content }}</div>
        <p v-if="currentPost.images?.length">图片：{{ currentPost.images.length }} 张</p>
        <p><strong>浏览/点赞/评论：</strong>{{ currentPost.view_count }} / {{ currentPost.like_count }} / {{ currentPost.comment_count }}</p>
      </template>
    </el-dialog>
    <el-dialog v-model="rejectVisible" title="拒绝原因" width="400px" aria-label="拒绝原因对话框">
      <el-input
        v-model="rejectReason"
        type="textarea"
        placeholder="请输入拒绝原因（选填，最多500字）"
        :rows="3"
        maxlength="500"
        show-word-limit
        aria-label="拒绝原因"
      />
      <template #footer>
        <el-button aria-label="取消拒绝" @click="rejectVisible = false">取消</el-button>
        <el-button type="primary" aria-label="确认拒绝" @click="confirmReject">确定拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getPosts,
  getPost,
  updatePostStatus,
  deletePost as deletePostApi,
  getComments,
  updateCommentRisk,
  type AdminPostListItem,
  type AdminCommentListItem,
} from '@/api/admin'
import { formatDate } from '@/utils/format'

const activeTab = ref<'posts' | 'comments'>('posts')

// 帖子待审
const postsLoading = ref(false)
const posts = ref<AdminPostListItem[]>([])
const postsTotal = ref(0)
const postsPage = ref(1)
const postsPageSize = ref(20)
const postDetailVisible = ref(false)
const currentPost = ref<AdminPostListItem | null>(null)

// 评论待审
const commentsLoading = ref(false)
const comments = ref<AdminCommentListItem[]>([])
const commentsTotal = ref(0)
const commentsPage = ref(1)
const commentsPageSize = ref(20)

// 拒绝弹窗（帖子和评论共用）
const rejectVisible = ref(false)
const rejectReason = ref('')
const rejectTargetPost = ref<AdminPostListItem | null>(null)
const rejectTargetComment = ref<AdminCommentListItem | null>(null)

async function fetchPosts() {
  postsLoading.value = true
  try {
    const { items, total } = await getPosts({
      risk_status: 'pending',
      limit: postsPageSize.value,
      offset: (postsPage.value - 1) * postsPageSize.value,
    })
    posts.value = items
    postsTotal.value = total
  } finally {
    postsLoading.value = false
  }
}

async function fetchComments() {
  commentsLoading.value = true
  try {
    const { items, total } = await getComments({
      risk_status: 'pending',
      limit: commentsPageSize.value,
      offset: (commentsPage.value - 1) * commentsPageSize.value,
    })
    comments.value = items
    commentsTotal.value = total
  } finally {
    commentsLoading.value = false
  }
}

function openPostDetail(row: AdminPostListItem) {
  getPost(row.id).then((post) => {
    currentPost.value = post
    postDetailVisible.value = true
  }).catch(() => ElMessage.error('获取详情失败'))
}

async function approvePost(row: AdminPostListItem) {
  try {
    await updatePostStatus(row.id, { risk_status: 'approved' })
    ElMessage.success('已通过')
    await fetchPosts()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '帖子不存在' : '操作失败')
  }
}

function rejectPost(row: AdminPostListItem) {
  rejectTargetPost.value = row
  rejectTargetComment.value = null
  rejectReason.value = ''
  rejectVisible.value = true
}

async function confirmReject() {
  // 验证拒绝原因
  const reason = rejectReason.value.trim()
  if (reason && reason.length > 500) {
    ElMessage.error('拒绝原因不能超过500字')
    return
  }

  if (rejectTargetPost.value) {
    try {
      await updatePostStatus(rejectTargetPost.value.id, {
        risk_status: 'rejected',
        risk_reason: reason || undefined,
      })
      ElMessage.success('已拒绝')
      rejectVisible.value = false
      rejectTargetPost.value = null
      rejectReason.value = ''
      await fetchPosts()
    } catch (e: unknown) {
      const err = e as { response?: { status: number } }
      ElMessage.error(err.response?.status === 404 ? '帖子不存在' : '操作失败')
    }
    return
  }
  if (rejectTargetComment.value) {
    try {
      await updateCommentRisk(rejectTargetComment.value.id, {
        risk_status: 'rejected',
        risk_reason: reason || undefined,
      })
      ElMessage.success('已拒绝')
      rejectVisible.value = false
      rejectTargetComment.value = null
      rejectReason.value = ''
      await fetchComments()
    } catch (e: unknown) {
      const err = e as { response?: { status: number } }
      ElMessage.error(err.response?.status === 404 ? '评论不存在' : '操作失败')
    }
  }
}

async function hidePost(row: AdminPostListItem) {
  try {
    await updatePostStatus(row.id, { status: 'hidden' })
    ElMessage.success('已隐藏')
    await fetchPosts()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '帖子不存在' : '操作失败')
  }
}

function deletePost(row: AdminPostListItem) {
  ElMessageBox.confirm('确定删除该帖子？', '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      await deletePostApi(row.id)
      ElMessage.success('已删除')
      await fetchPosts()
    } catch (e: unknown) {
      const err = e as { response?: { status: number } }
      ElMessage.error(err.response?.status === 404 ? '帖子不存在' : '删除失败')
    }
  }).catch(() => {})
}

async function approveComment(row: AdminCommentListItem) {
  try {
    await updateCommentRisk(row.id, { risk_status: 'approved' })
    ElMessage.success('已通过')
    await fetchComments()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '评论不存在' : '操作失败')
  }
}

function rejectComment(row: AdminCommentListItem) {
  rejectTargetComment.value = row
  rejectTargetPost.value = null
  rejectReason.value = ''
  rejectVisible.value = true
}

onMounted(() => {
  fetchPosts()
  fetchComments()
})
watch(activeTab, (name) => {
  if (name === 'posts') fetchPosts()
  else fetchComments()
})
</script>

<style scoped>
.page-title { margin-bottom: 16px; font-size: 18px; }
.toolbar { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: flex-end; }
.content-block { white-space: pre-wrap; max-height: 200px; overflow: auto; }
</style>
