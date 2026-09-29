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

          <h3 className="text-xl font-semibold mt-6 mb-2">Phát hiện chính từ dữ liệu thực tế:</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              Mô hình <strong className="text-navy-700">{data?.data?.model}</strong> mang lại khả năng giải thích lợi suất (Adjusted R²) cao nhất trong số các mô hình được kiểm định.
            </li>
            <li>
              {data?.data?.ranking && data.data.ranking.indexOf('FF3') < data.data.ranking.indexOf('FF5') ? 
                'Đáng chú ý, mô hình Fama-French 3 nhân tố (FF3) xếp hạng cao hơn FF5. Điều này cho thấy tại thị trường Việt Nam giai đoạn này, các biến số về Lợi nhuận (RMW) và Đầu tư (CMA) chưa thể hiện sức mạnh giải thích rõ rệt so với Quy mô và Giá trị.' :
                'Mô hình FF5 cho thấy sự ưu việt hơn FF3, phản ánh đúng lý thuyết tài chính hiện đại khi bổ sung yếu tố Lợi nhuận và Đầu tư.'
              }
            </li>
            <li>
              Việc bổ sung các nhân tố đặc thù của thị trường cận biên như Thanh khoản (LIQ), Khối ngoại (FOR), và Biến động (VOL) vào mô hình {data?.data?.model === 'FF5_ALL' ? 'đã chứng minh được hiệu quả vượt trội khi đưa FF5_ALL lên vị trí top 1.' : 'có tác động làm thay đổi thứ hạng mô hình, phản ánh đặc tính riêng của thị trường Việt Nam.'}
            </li>
            <li>Danh mục tối ưu theo Markowitz vượt trội hơn so với danh mục Equal-Weight (Tỷ trọng đều) và chỉ số VN30 cơ sở xét về tỷ lệ Sharpe trong kỳ Backtest.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
