import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { MODELS } from '../lib/constants';

const schema = z.object({
  model: z.string(),
  estimator: z.enum(['sample', 'ledoit_wolf', 'semi']),
  w_max: z.number().min(0.04).max(1),
  fee_buy: z.number().min(0).max(0.1),
  fee_sell: z.number().min(0).max(0.1),
  train_start: z.string(),
  train_end: z.string(),
  test_start: z.string(),
  test_end: z.string(),
  frequency: z.enum(['M', 'Q']),
  data_freq: z.enum(['daily', 'weekly', 'monthly']),
  cov_type: z.enum(['HAC', 'nonrobust']),
}).refine((values) => values.train_start <= values.train_end, {
  message: 'Ngày bắt đầu Train phải trước hoặc bằng ngày kết thúc.',
  path: ['train_end'],
}).refine((values) => values.test_start <= values.test_end, {
  message: 'Ngày bắt đầu Backtest phải trước hoặc bằng ngày kết thúc.',
  path: ['test_end'],
});

export type ConfigValues = z.infer<typeof schema>;

export default function ConfigPanel({ onSubmit, defaultValues, isLoading, showTestDates = false, disabledReason, regressionMode = false, hideFees = false }: { onSubmit: (data: ConfigValues) => void, defaultValues?: Partial<ConfigValues>, isLoading?: boolean, showTestDates?: boolean, disabledReason?: string, regressionMode?: boolean, hideFees?: boolean }) {
  const { register, handleSubmit, setError, watch, formState: { errors } } = useForm<ConfigValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      model: 'FF5',
      estimator: 'ledoit_wolf',
      w_max: 0.15,
      fee_buy: 0.0015,
      fee_sell: 0.0025,
      train_start: '2021-01-01',
      train_end: '2024-12-31',
      test_start: '2025-01-01',
      test_end: '2025-12-31',
      frequency: 'M',
      data_freq: 'daily',
      cov_type: 'HAC',
      ...defaultValues,
    }
  });

  const w_max = watch('w_max');
  const submit = handleSubmit((values) => {
    if (showTestDates && values.test_start <= values.train_end) {
      setError('test_start', {
        type: 'validate',
        message: 'Backtest phải bắt đầu sau khi giai đoạn Train kết thúc.',
      });
      return;
    }
    onSubmit(values);
  });

  return (
    <form onSubmit={submit} className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 space-y-4">
      <h3 className="text-lg font-medium text-slate-800 border-b pb-2">Bảng Cấu Hình</h3>
      
      <div>
        <label className="block text-sm font-medium text-slate-700">Mô hình (Model)</label>
        <select {...register('model')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-navy-500 focus:ring-navy-500 sm:text-sm p-2 border">
          {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {!regressionMode && (
        <>
      <div>
        <label className="block text-sm font-medium text-slate-700">Ước lượng rủi ro (Estimator)</label>
        <select {...register('estimator')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-navy-500 focus:ring-navy-500 sm:text-sm p-2 border">
          <option value="sample">Mẫu (Sample Covariance)</option>
          <option value="ledoit_wolf">Ledoit-Wolf Shrinkage</option>
          <option value="semi">Bán phương sai (Semi-Covariance)</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700">Tỷ trọng tối đa / mã (w_max): <span className="font-bold text-navy-600">{(w_max * 100).toFixed(1)}%</span></label>
        <input type="range" min="0.04" max="1" step="0.01" {...register('w_max', { valueAsNumber: true })} className="mt-1 block w-full" />
      </div>

          {!hideFees && (
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Phí mua</label>
          <input type="number" min="0" max="0.1" step="0.0001" {...register('fee_buy', { valueAsNumber: true })} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-navy-500 focus:ring-navy-500 sm:text-sm p-2 border" />
          {errors.fee_buy && <p className="mt-1 text-xs text-red-600">Phí mua phải nằm trong khoảng 0–10%.</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Phí bán</label>
          <input type="number" min="0" max="0.1" step="0.0001" {...register('fee_sell', { valueAsNumber: true })} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-navy-500 focus:ring-navy-500 sm:text-sm p-2 border" />
          {errors.fee_sell && <p className="mt-1 text-xs text-red-600">Phí bán phải nằm trong khoảng 0–10%.</p>}
        </div>
      </div>

          )}
        </>
      )}

      {regressionMode && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Tần suất dữ liệu</label>
            <select {...register('data_freq')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border">
              <option value="daily">Ngày (Daily)</option>
              <option value="weekly">Tuần (Weekly)</option>
              <option value="monthly">Tháng (Monthly)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Sai số chuẩn</label>
            <select {...register('cov_type')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border">
              <option value="HAC">HAC (Newey-West)</option>
              <option value="nonrobust">OLS (Thường)</option>
            </select>
          </div>
        </div>
      )}

      {showTestDates && (
        <div className="space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Bắt đầu Backtest</label>
            <input type="date" {...register('test_start')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border" />
            {errors.test_start && <p className="mt-1 text-xs text-red-600">{errors.test_start.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Kết thúc Backtest</label>
            <input type="date" {...register('test_end')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border" />
          </div>
          {errors.test_end && <p className="col-span-2 text-xs text-red-600">{errors.test_end.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Tần suất tái cân bằng</label>
          <select {...register('frequency')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border">
            <option value="M">Hàng tháng</option>
            <option value="Q">Hàng quý</option>
          </select>
        </div>
        </div>
      )}
      {errors.train_end && <p className="text-xs text-red-600">{errors.train_end.message}</p>}
      {disabledReason && <p className="text-xs text-amber-700">{disabledReason}</p>}
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Bắt đầu Train</label>
          <input type="date" {...register('train_start')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Kết thúc Train</label>
          <input type="date" {...register('train_end')} className="mt-1 block w-full rounded-md border-slate-300 shadow-sm sm:text-sm p-2 border" />
        </div>
      </div>
      
      <button type="submit" disabled={isLoading || !!disabledReason} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-navy-600 hover:bg-navy-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-500 disabled:opacity-50">
        {isLoading ? 'Đang xử lý...' : disabledReason || 'Chạy thuật toán'}
      </button>
    </form>
  );
}
