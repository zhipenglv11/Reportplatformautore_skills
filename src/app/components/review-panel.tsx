import { useState } from 'react';
import { 
  CircleCheck, 
  CircleX, 
  Clock, 
  FileText, 
  User, 
  Calendar,
  ChevronRight,
  ChevronDown,
  Edit3,
  Send,
  MoreHorizontal
} from 'lucide-react';

interface ReviewItem {
  id: string;
  title: string;
  status: 'pending' | 'approved' | 'rejected';
  submitter: string;
  date: string;
  chapters: ChapterItem[];
}

interface ChapterItem {
  id: string;
  title: string;
  number: string;
}

interface Comment {
  id: string;
  author: string;
  avatar: string;
  content: string;
  timestamp: string;
  tag?: string;
  tagColor?: string;
}

const mockReviews: ReviewItem[] = [
  {
    id: '1',
    title: '工业生产线安全评估报告',
    status: 'pending',
    submitter: '张工程师',
    date: '2024-12-24',
    chapters: [
      { id: '1-1', number: '1', title: '项目概述' },
      { id: '1-2', number: '2', title: '安全风险评估' },
      { id: '1-3', number: '3', title: '设备检查结果' },
      { id: '1-4', number: '4', title: '整改建议' },
      { id: '1-5', number: '5', title: '应急预案' },
      { id: '1-6', number: '6', title: '结论与签署' },
    ],
  },
  {
    id: '2',
    title: '设备维护检查报告',
    status: 'approved',
    submitter: '李工程师',
    date: '2024-12-23',
    chapters: [
      { id: '2-1', number: '1', title: '维护范围' },
      { id: '2-2', number: '2', title: '检查记录' },
      { id: '2-3', number: '3', title: '问题汇总' },
      { id: '2-4', number: '4', title: '维护建议' },
    ],
  },
  {
    id: '3',
    title: '质量控制月度报告',
    status: 'pending',
    submitter: '王工程师',
    date: '2024-12-22',
    chapters: [
      { id: '3-1', number: '1', title: '质量指标概览' },
      { id: '3-2', number: '2', title: '检测数据分析' },
      { id: '3-3', number: '3', title: '不合格项处理' },
      { id: '3-4', number: '4', title: '改进措施' },
      { id: '3-5', number: '5', title: '下月计划' },
      { id: '3-6', number: '6', title: '质量趋势' },
      { id: '3-7', number: '7', title: '人员培训' },
      { id: '3-8', number: '8', title: '总结' },
    ],
  },
];

export default function ReviewPanel() {
  const [reviews] = useState<ReviewItem[]>(mockReviews);
  const [selectedReview, setSelectedReview] = useState<ReviewItem | null>(null);
  const [expandedReviews, setExpandedReviews] = useState<Set<string>>(new Set());
  const [selectedChapter, setSelectedChapter] = useState<string | null>(null);
  const [newComment, setNewComment] = useState('');
  const [comments, setComments] = useState<Comment[]>([
    {
      id: '1',
      author: '张工程师',
      avatar: '张',
      content: '八月的增长看起来与原始CSV数据相比有点奇怪。我们能否仔细检查SQL节点？',
      timestamp: '2小时前',
      tag: '图表标注',
      tagColor: 'bg-orange-50 text-orange-600 border-orange-200'
    },
    {
      id: '2',
      author: '李工程师',
      avatar: '李',
      content: '医疗保健收入似乎是正确的，但增长率计算可能有一个小数点的问题',
      timestamp: '5小时前',
      tag: '表格行 #1',
      tagColor: 'bg-blue-50 text-blue-600 border-blue-200'
    },
    {
      id: '3',
      author: '王工程师',
      avatar: '王',
      content: '很好！我会更新转换节点中的公式。',
      timestamp: '18分钟前',
    }
  ]);

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'pending':
        return { 
          icon: Clock, 
          color: 'text-amber-600', 
          bg: 'bg-amber-50', 
          border: 'border-amber-200',
          label: '待审核' 
        };
      case 'approved':
        return { 
          icon: CircleCheck, 
          color: 'text-green-600', 
          bg: 'bg-green-50', 
          border: 'border-green-200',
          label: '已通过' 
        };
      case 'rejected':
        return { 
          icon: CircleX, 
          color: 'text-red-600', 
          bg: 'bg-red-50', 
          border: 'border-red-200',
          label: '已驳回' 
        };
      default:
        return { 
          icon: Clock, 
          color: 'text-slate-600', 
          bg: 'bg-slate-50', 
          border: 'border-slate-200',
          label: '未知' 
        };
    }
  };

  const toggleExpand = (reviewId: string) => {
    const newExpanded = new Set(expandedReviews);
    if (newExpanded.has(reviewId)) {
      newExpanded.delete(reviewId);
    } else {
      newExpanded.add(reviewId);
    }
    setExpandedReviews(newExpanded);
  };

  const handleReviewClick = (review: ReviewItem) => {
    setSelectedReview(review);
    if (!expandedReviews.has(review.id)) {
      toggleExpand(review.id);
    }
  };

  const handleAddComment = () => {
    if (newComment.trim()) {
      const comment: Comment = {
        id: Date.now().toString(),
        author: '当前用户',
        avatar: '我',
        content: newComment,
        timestamp: '刚刚'
      };
      setComments([comment, ...comments]);
      setNewComment('');
    }
  };

  const handleApprove = () => {
    if (selectedReview) {
      // TODO: 实际审批逻辑
      alert('报告已批准');
    }
  };

  const handleReject = () => {
    if (selectedReview) {
      // TODO: 实际驳回逻辑
      alert('报告已驳回');
    }
  };

  const handleRequestEdit = () => {
    if (selectedReview) {
      // TODO: 实际请求编辑逻辑
      alert('已请求编辑');
    }
  };

  return (
    <div className="flex h-full bg-slate-50">
      {/* Left Sidebar - Review List with Expandable Chapters */}
      <div className="w-96 bg-white border-r border-slate-200 overflow-y-auto flex-shrink-0">
        <div className="p-4 border-b border-slate-200">
          <h3 className="text-slate-800 font-semibold">待审核报告</h3>
          <p className="text-sm text-slate-500 mt-1">
            {reviews.filter(r => r.status === 'pending').length} 份待审核
          </p>
        </div>

        <div className="p-4 space-y-2">
          {reviews.map((review) => {
            const statusConfig = getStatusConfig(review.status);
            const StatusIcon = statusConfig.icon;
            const isExpanded = expandedReviews.has(review.id);
            const isSelected = selectedReview?.id === review.id;

            return (
              <div key={review.id}>
                {/* Review Item */}
                <div
                  className={`rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <button
                    onClick={() => handleReviewClick(review)}
                    className="w-full p-4 text-left"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-start gap-2 flex-1">
                        <div
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleExpand(review.id);
                          }}
                          className="mt-1 hover:bg-slate-200 rounded p-0.5 transition-colors cursor-pointer"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-slate-600" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-slate-600" />
                          )}
                        </div>
                        <h4 className="text-slate-800 font-medium pr-2">{review.title}</h4>
                      </div>
                      <div className={`flex items-center gap-1 px-2 py-1 rounded ${statusConfig.bg} ${statusConfig.border} border flex-shrink-0`}>
                        <StatusIcon className={`w-3 h-3 ${statusConfig.color}`} />
                        <span className={`text-xs ${statusConfig.color} font-medium`}>{statusConfig.label}</span>
                      </div>
                    </div>

                    <div className="space-y-1 ml-6">
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <User className="w-4 h-4" />
                        {review.submitter}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <Calendar className="w-4 h-4" />
                        {review.date}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <FileText className="w-4 h-4" />
                        {review.chapters.length} 个章节
                      </div>
                    </div>
                  </button>

                  {/* Expandable Chapter List */}
                  {isExpanded && (
                    <div className="border-t border-slate-200 bg-slate-50">
                      <div className="p-2 space-y-1">
                        {review.chapters.map((chapter) => (
                          <button
                            key={chapter.id}
                            onClick={() => setSelectedChapter(chapter.id)}
                            className={`w-full text-left px-3 py-2 rounded transition-all ${
                              selectedChapter === chapter.id
                                ? 'bg-blue-100 text-blue-900'
                                : 'hover:bg-slate-100 text-slate-700'
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono text-slate-500 w-6">
                                {chapter.number}
                              </span>
                              <span className="text-sm">{chapter.title}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Center - Review Detail */}
      <div className="flex-1 overflow-y-auto">
        {selectedReview ? (
          <div className="p-8 bg-slate-100">
            {/* Word Document Style Container */}
            <div className="max-w-4xl mx-auto bg-white shadow-lg" style={{ minHeight: '297mm' }}>
              {/* Document Content - A4 Paper Style */}
              <div className="p-16">
                {/* Document Header */}
                <div className="mb-12">
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex-1">
                      <h1 className="text-4xl font-bold text-slate-900 mb-3">
                        {selectedReview.title}
                      </h1>
                      <p className="text-slate-600">准备给：执行领导团队</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-slate-900 mb-1">2023年第三季度</div>
                      <div className="text-slate-600">北美地区</div>
                    </div>
                  </div>
                  <div className="h-0.5 bg-slate-900"></div>
                </div>

                {/* Chapter 1 - Revenue Overview */}
                <div className="mb-12">
                  <div className="flex items-center gap-3 mb-6">
                    <h2 className="text-2xl font-bold text-slate-900">1. 收入概览</h2>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded uppercase tracking-wide">
                      自动化
                    </span>
                  </div>

                  <p className="text-slate-700 leading-relaxed mb-8 text-justify">
                    北美地区在市场逆风中展现了强劲的增长。本季度总收入达到 <span className="font-semibold text-slate-900">$4.2M</span>，
                    代表 <span className="font-semibold text-green-600">12%的同比增长</span>。主要驱动力是企业细分市场，
                    其表现超出预期15%。尽管面临宏观经济挑战，我们的销售团队成功地在关键垂直领域获得了新客户，
                    特别是在医疗保健和金融科技行业。
                  </p>

                  {/* Bar Chart */}
                  <div className="bg-slate-50 rounded-lg p-8 border border-slate-200 mb-6">
                    <div className="flex items-end justify-around h-80 px-8">
                      {/* July */}
                      <div className="flex flex-col items-center flex-1 max-w-36">
                        <div className="w-full bg-gradient-to-t from-blue-200 to-blue-100 rounded-t-lg relative" style={{ height: '45%' }}>
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-sm font-semibold text-slate-700">
                            $1.3M
                          </div>
                        </div>
                        <div className="mt-4 text-slate-600">七月</div>
                      </div>

                      {/* August */}
                      <div className="flex flex-col items-center flex-1 max-w-36">
                        <div className="w-full bg-gradient-to-t from-blue-300 to-blue-200 rounded-t-lg relative" style={{ height: '60%' }}>
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-sm font-semibold text-slate-700">
                            $1.6M
                          </div>
                        </div>
                        <div className="mt-4 text-slate-600">八月</div>
                      </div>

                      {/* September */}
                      <div className="flex flex-col items-center flex-1 max-w-36">
                        <div className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg relative flex items-center justify-center" style={{ height: '100%' }}>
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-sm font-semibold text-slate-900">
                            $1.7M
                          </div>
                          {/* Highlight Badge */}
                          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                            <div className="w-14 h-14 bg-amber-400 rounded-full flex items-center justify-center shadow-lg">
                              <svg className="w-7 h-7 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                              </svg>
                            </div>
                          </div>
                        </div>
                        <div className="mt-4 text-slate-900 font-semibold">九月</div>
                      </div>
                    </div>
                  </div>

                  <p className="text-slate-700 leading-relaxed text-justify">
                    如图所示，九月份的收入达到了本季度的峰值，这得益于几个大型企业合同的成功签约。
                    销售周期的缩短和转化率的提高都表明我们的销售策略正在产生积极效果。
                  </p>
                </div>

                {/* Chapter 2 - Top Performing Verticals */}
                <div className="mb-12">
                  <h2 className="text-2xl font-bold text-slate-900 mb-6">2. 表现最佳垂直行业</h2>

                  <p className="text-slate-700 leading-relaxed mb-6 text-justify">
                    本季度，我们在多个垂直行业都取得了显著进展。医疗保健行业继续保持强劲增长势头，
                    成为我们最大的收入来源。金融科技行业展现出令人印象深刻的增长率，而零售行业虽然面临挑战，
                    但仍然是我们战略重点之一。
                  </p>

                  {/* Table */}
                  <div className="overflow-hidden border border-slate-200 rounded-lg mb-6">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                          <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">垂直行业</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">成交数量</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">收入</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">增长</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        <tr className="hover:bg-slate-50 transition-colors border-l-4 border-l-amber-400 bg-amber-50/30">
                          <td className="px-6 py-4 text-slate-900 font-medium">医疗保健</td>
                          <td className="px-6 py-4 text-slate-700">45</td>
                          <td className="px-6 py-4 text-slate-700">$1.2M</td>
                          <td className="px-6 py-4 text-green-600 font-semibold">+8.5%</td>
                        </tr>
                        <tr className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 text-slate-900 font-medium">金融科技</td>
                          <td className="px-6 py-4 text-slate-700">32</td>
                          <td className="px-6 py-4 text-slate-700">$980k</td>
                          <td className="px-6 py-4 text-green-600 font-semibold">+14.2%</td>
                        </tr>
                        <tr className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 text-slate-900 font-medium">零售</td>
                          <td className="px-6 py-4 text-slate-700">28</td>
                          <td className="px-6 py-4 text-slate-700">$750k</td>
                          <td className="px-6 py-4 text-red-600 font-semibold">-2.1%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <p className="text-slate-700 leading-relaxed text-justify mb-4">
                    医疗保健行业的强劲表现主要归因于我们的专业化销售团队和定制化解决方案。
                    该行业的客户保留率达到95%，显示出极高的客户满意度。
                  </p>

                  <p className="text-slate-700 leading-relaxed text-justify">
                    金融科技行业虽然成交数量较少，但展现出最高的增长率（+14.2%），这表明该领域存在巨大的市场机会。
                    我们计划在下季度加大对该行业的投资和资源配置。
                  </p>
                </div>

                {/* Chapter 3 - Key Insights */}
                <div className="mb-12">
                  <h2 className="text-2xl font-bold text-slate-900 mb-6">3. 关键洞察与建议</h2>

                  <div className="space-y-4 mb-6">
                    <div className="flex gap-3">
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-slate-700 leading-relaxed text-justify">
                        <span className="font-semibold">企业细分市场机会：</span>
                        大型企业客户的销售周期虽然较长，但订单价值显著更高。建议增加对企业销售团队的培训和支持。
                      </p>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-slate-700 leading-relaxed text-justify">
                        <span className="font-semibold">产品创新需求：</span>
                        客户反馈表明需要更灵活的定价方案和更强大的集成功能。产品团队应优先考虑这些改进。
                      </p>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-slate-700 leading-relaxed text-justify">
                        <span className="font-semibold">市场扩张策略：</span>
                        金融科技和医疗保健行业的成功经验可以复制到其他垂直领域，特别是教育和制造业。
                      </p>
                    </div>
                  </div>
                </div>

                {/* Chapter 4 - Conclusion */}
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-slate-900 mb-6">4. 结论</h2>

                  <p className="text-slate-700 leading-relaxed text-justify mb-4">
                    第三季度的表现超出了我们的预期，总收入达到$4.2M，同比增长12%。
                    我们在关键垂直行业建立了强大的市场地位，客户满意度持续提高。
                  </p>

                  <p className="text-slate-700 leading-relaxed text-justify mb-6">
                    展望第四季度，我们将继续专注于企业细分市场，加强产品创新，
                    并探索新的垂直行业机会。预计Q4收入将达到$4.5M，全年收入目标有望提前实现。
                  </p>

                  <div className="border-t border-slate-300 pt-6 mt-8">
                    <div className="grid grid-cols-2 gap-8">
                      <div>
                        <p className="text-sm text-slate-600 mb-2">报告编制人</p>
                        <p className="text-slate-900 font-semibold">{selectedReview.submitter}</p>
                        <p className="text-sm text-slate-500">{selectedReview.date}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600 mb-2">审核状态</p>
                        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded ${getStatusConfig(selectedReview.status).bg} ${getStatusConfig(selectedReview.status).border} border`}>
                          {(() => {
                            const StatusIcon = getStatusConfig(selectedReview.status).icon;
                            return <StatusIcon className={`w-4 h-4 ${getStatusConfig(selectedReview.status).color}`} />;
                          })()}
                          <span className={`text-sm font-medium ${getStatusConfig(selectedReview.status).color}`}>
                            {getStatusConfig(selectedReview.status).label}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">请从左侧选择一份报告进行审核</p>
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar - Approval Workflow & Comments */}
      {selectedReview && (
        <div className="w-80 bg-white border-l border-slate-200 flex flex-col flex-shrink-0">
          {/* Approval Workflow */}
          <div className="p-5 border-b border-slate-200">
            <h3 className="text-slate-900 font-semibold mb-4">审批工作流</h3>
            
            <div className="space-y-3">
              {/* Approve Button */}
              <button 
                onClick={handleApprove}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm font-medium"
              >
                <CircleCheck className="w-5 h-5" />
                批准报告
              </button>

              {/* Request Edit & Reject Buttons */}
              <div className="grid grid-cols-2 gap-2">
                <button 
                  onClick={handleRequestEdit}
                  className="py-2.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm border border-slate-200"
                >
                  <Edit3 className="w-4 h-4" />
                  请求编辑
                </button>
                <button 
                  onClick={handleReject}
                  className="py-2.5 bg-white hover:bg-red-50 text-red-600 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm border border-red-200 hover:border-red-300"
                >
                  <CircleX className="w-4 h-4" />
                  驳回
                </button>
              </div>
            </div>
          </div>

          {/* Comments Section */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Comments Header */}
            <div className="p-5 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="text-slate-900 font-semibold">评论</h4>
                <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs font-medium rounded-full">
                  {comments.length}
                </span>
              </div>
              <button className="text-slate-400 hover:text-slate-600 transition-colors">
                <MoreHorizontal className="w-5 h-5" />
              </button>
            </div>

            {/* Comments List */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {comments.map((comment) => (
                <div key={comment.id} className="group">
                  <div className="flex items-start gap-3">
                    {/* Avatar */}
                    <div className="w-8 h-8 bg-gradient-to-br from-slate-600 to-slate-700 rounded-full flex items-center justify-center text-white text-xs font-medium flex-shrink-0">
                      {comment.avatar}
                    </div>
                    
                    {/* Comment Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-900">{comment.author}</span>
                        <span className="text-xs text-slate-400">{comment.timestamp}</span>
                      </div>
                      
                      {/* Tag */}
                      {comment.tag && (
                        <div className="mb-2">
                          <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border ${comment.tagColor}`}>
                            {comment.tag}
                          </span>
                        </div>
                      )}
                      
                      {/* Comment Text */}
                      <p className="text-sm text-slate-700 leading-relaxed">{comment.content}</p>
                      
                      {/* Reply Button */}
                      <button className="text-xs text-slate-500 hover:text-blue-600 mt-2 transition-colors font-medium">
                        回复
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Add Comment */}
            <div className="p-4 border-t border-slate-200 bg-white">
              <div className="flex items-start gap-2 mb-2">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                  placeholder="添加评论..."
                  className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                />
                <button 
                  onClick={handleAddComment}
                  disabled={!newComment.trim()}
                  className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-500">
                <button className="hover:text-slate-700 transition-colors">粗体</button>
                <button className="hover:text-slate-700 transition-colors">@提及</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}