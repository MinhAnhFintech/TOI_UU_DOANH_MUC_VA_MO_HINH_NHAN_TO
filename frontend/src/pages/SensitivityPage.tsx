import ChartCard from '../components/ChartCard';

export default function SensitivityPage() {
  return (
    <div className="space-y-6">
      <ChartCard title="Phân tích Độ nhạy (Tỷ trọng tối đa vs Các phương pháp ước lượng)">
        <div className="p-8 text-center text-slate-500">
          Chưa có dữ liệu phân tích độ nhạy. (Tính năng đang được phát triển)
        </div>
      </ChartCard>
    </div>
  );
}
