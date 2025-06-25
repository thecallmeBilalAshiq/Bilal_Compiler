declare i32 @printf(i8*, ...)
declare i32 @scanf(i8*, ...)
@.in = constant [3 x i8] c"%d\00"
@.out = constant [4 x i8] c"%d\0A\00"

define i32 @main() {
entry:
  %a = alloca i32
  call i32 (i8*, ...) @scanf(i8* getelementptr ([3 x i8], [3 x i8]* @.in, i32 0, i32 0), i32* %a)
  %r0 = icmp sgt i32 %a, 0
  %r1 = zext i1 %r0 to i32
  %t0 = alloca i32
  store i32 %r1, i32* %t0
  %cond = load i32, i32* %t0
  %check = icmp eq i32 %cond, 0
  br i1 %check, label %else0, label %next2
next2:
  %r3 = load i32, i32* %1
  call i32 (i8*, ...) @printf(i8* getelementptr ([4 x i8], [4 x i8]* @.out, i32 0, i32 0), i32 %r3)
  br label %ifend1
  br label %else0
else0:
  %r4 = load i32, i32* %0
  call i32 (i8*, ...) @printf(i8* getelementptr ([4 x i8], [4 x i8]* @.out, i32 0, i32 0), i32 %r4)
  br label %ifend1
ifend1:
  ret i32 0
  ret i32 0
}