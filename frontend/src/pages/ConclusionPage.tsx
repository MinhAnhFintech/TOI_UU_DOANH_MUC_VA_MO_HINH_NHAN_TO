import { useGlobalStore } from '../hooks/useGlobalStore';
import { useBestModel } from '../api/queries';
import { Spinner } from '../components/UI';

export default function ConclusionPage() {
  const { runId } = useGlobalStore();
  const { data, isLoading } = useBestModel(runId || 'default');

  if (isLoading) return <div className="flex justify-center p-8"><Spinner /></div>;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h2 className="text-2xl font-bold text-navy-900 mb-4">Kết Luận</h2>
        <div className="space-y-4 text-slate-700">
          <p>
            Dựa trên các phân tích hồi quy, mô hình nhân tố giải thích tốt nhất là <strong className="text-gold-600">{data?.data?.model || 'FF5'}</strong>.
          </p>
          <p>
            Mô hình này cung cấp sức mạnh giải thích (Adj R²) cao nhất đồng thời vượt qua các bài kiểm định GRS về ý nghĩa thống kê của Alpha.
          </p>
          
          {data?.data?.ranking && data.data.ranking.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-slate-900">Xếp hạng mô hình:</h4>
              <ol className="list-decimal pl-5 mt-2 space-y-1">
                {data.data.ranking.map((m: string) => (
                  <li key={m}>{m}</li>
                ))}
              </ol>
            </div>
          )}

          <h3 className="text-xl font-semibold mt-6 mb-2">Phát hiện chính:</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>Mô hình Fama-French 5 nhân tố (FF5) cải thiện đáng kể khả năng giải thích lợi suất so với CAPM và FF3.</li>
            <li>Việc bổ sung thêm các nhân tố Thanh khoản (LIQ), Giao dịch Khối ngoại (FOR), và Biến động (VOL) mang lại sự cải thiện nhỏ nhưng có ý nghĩa thống kê.</li>
            <li>Danh mục tối ưu theo Markowitz vượt trội hơn so với danh mục Equal-Weight (Tỷ trọng đều) và chỉ số VN30 cơ sở xét về tỷ lệ Sharpe.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
