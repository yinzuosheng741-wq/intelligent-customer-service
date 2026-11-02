import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "智能客服 · 电商客服知识助手",
  description: "面向比价导购、二手鉴定、售后理赔和订单服务的电商客服知识助手",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
