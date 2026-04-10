-- DANGER: This creates an infinite loop to max out CPU
-- Run this in a new query window right before you hit "Analyze" in the UI.
DECLARE @i INT = 1, @a INT, @count INT;
WHILE (1=1) 
BEGIN
    SET @count = 0; SET @a = 1;
    WHILE (@a <= @i) 
    BEGIN
        IF (@i % @a = 0) SET @count = @count + 1;
        SET @a = @a + 1;
    END
    SET @i = @i + 1;
END